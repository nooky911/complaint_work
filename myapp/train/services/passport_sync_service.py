import asyncio
import logging
import re
from collections import defaultdict
from sqlalchemy import select, text

from myapp.services.omega_services.product_passport_equipment_service import (
    ProductPassportEquipmentService,
)
from myapp.train.services.equipment_service import equipment_details
from myapp.config import settings
from myapp.database.base import async_session_maker
from myapp.integrations.ul.client import ULServiceClient
from myapp.integrations.omega.client import OmegaClient
from myapp.models.product_passports import ProductPassport, ProductPassportNode
from myapp.train.models.train_models import TrainModel
from myapp.validators.product_passport_validator import ProductPassportValidator

logger = logging.getLogger("uvicorn.error")
_sync_lock = asyncio.Lock()


def parse_train_identity(name):
    """Разбирает номер и модель без потери исполнения и исключает шаблоны"""
    if "ШАБЛОН" in name.upper():
        raise ValueError("Шаблоны импортировать нельзя")
    match = re.fullmatch(
        r"Электропоезд\s+ЭС(104|105)(П)?(?:-\d+)?\s*№\s*(\d+)(?:\s.*)?",
        name.strip(),
        re.I,
    )
    if not match:
        raise ValueError(f"Не разобрано название паспорта: {name}")
    model = "ЭС" + match[1] + (match[2] or "").upper()
    number = int(match[3])
    if number < (30 if model == "ЭС104" else 1):
        raise ValueError("Паспорт вне согласованного диапазона")
    return model, f"{number:03d}"


async def add_missing_train_passport(session, model, number, incoming):
    """Атомарно добавляет новый паспорт и не изменяет существующие экземпляры"""
    await session.execute(text("SELECT pg_advisory_xact_lock(20261029,1)"))
    model_id = await session.scalar(
        select(TrainModel.id).where(TrainModel.train_model_name == model)
    )
    if model_id is None:
        raise ValueError(f"Не найдена модель поездов {model}")
    existing = await session.scalar(
        select(ProductPassport.id).where(
            ProductPassport.train_model_id == model_id,
            ProductPassport.product_number == number,
        )
    )
    if existing:
        return {"added": 0, "skipped_existing": 1, "unmapped": 0}
    if await session.scalar(
        select(ProductPassport.id).where(
            ProductPassport.omega_root_code == incoming.omega_root_code
        )
    ):
        raise ValueError("Корень Omega уже принадлежит другому паспорту")
    if parse_train_identity(incoming.omega_name) != (model, number):
        raise ValueError("Модель или номер дерева Omega не совпали с запросом")
    ProductPassportValidator.validate_tree(incoming.nodes, incoming.omega_root_code)
    known = (
        await session.execute(
            select(ProductPassport.train_model_id, ProductPassportNode)
            .join(ProductPassportNode)
            .where(
                ProductPassport.train_model_id.is_not(None),
                ProductPassportNode.train_equipment_id.is_not(None),
            )
        )
    ).all()
    match_rules, serial_rules = ProductPassportEquipmentService.confirmed_match_rules(
        [node for _, node in known], equipment_field="train_equipment_id"
    )
    numbered_links = {}
    for known_model_id, node in known:
        ProductPassportEquipmentService.remember_numbered_link(
            numbered_links, known_model_id, node, equipment_field="train_equipment_id"
        )
    catalogue = await equipment_details(session)
    record = ProductPassport(
        product_type="Электропоезд",
        train_model_id=model_id,
        locomotive_model_id=None,
        product_number=number,
        omega_root_code=incoming.omega_root_code,
        omega_name=incoming.omega_name,
    )
    record.nodes = []
    for source in incoming.nodes:
        node = ProductPassportNode(
            **source.model_dump(),
            equipment_id=None,
            train_equipment_id=None,
            supplier_id=None,
        )
        match = ProductPassportEquipmentService.resolve_match(
            node, match_rules, serial_rules
        )
        if match is not None and match[0] in catalogue:
            node.train_equipment_id = match[0]
        record.nodes.append(node)
    ProductPassportEquipmentService.inherit_numbered_links(
        model_id, record.nodes, numbered_links, equipment_field="train_equipment_id"
    )
    redundant = ProductPassportEquipmentService.redundant_parents(
        [
            (0, node.omega_code, node.parent_omega_code, node.train_equipment_id)
            for node in record.nodes
        ]
    )
    for node in record.nodes:
        if (0, node.omega_code) in redundant:
            node.train_equipment_id = None
        if node.train_equipment_id in catalogue:
            node.supplier_id = catalogue[node.train_equipment_id]["supplier_id"]
    unmapped = sum(node.train_equipment_id is None for node in record.nodes)
    session.add(record)
    await session.flush()
    return {"added": 1, "skipped_existing": 0, "unmapped": unmapped}


async def sync_new_train_passports():
    """Загружает только отсутствующие поездные паспорта после появления в UL"""
    if _sync_lock.locked():
        return {"busy": 1}
    async with _sync_lock:
        identities = await asyncio.to_thread(ULServiceClient.get_train_identities)
        async with async_session_maker() as session:
            existing = {
                (model, f"{int(number):03d}")
                for model, number in (
                    await session.execute(
                        select(
                            TrainModel.train_model_name, ProductPassport.product_number
                        ).join(
                            ProductPassport,
                            ProductPassport.train_model_id == TrainModel.id,
                        )
                    )
                ).all()
            }
        missing = identities - existing
        result = dict(
            added=0,
            skipped_existing=len(identities & existing),
            waiting_for_omega=0,
            errors=0,
            unmapped=0,
        )
        if not missing:
            return result
        client = OmegaClient()
        roots = defaultdict(list)
        for root in await asyncio.to_thread(client.list_train_passport_roots):
            try:
                identity = parse_train_identity(root.omega_name)
            except ValueError:
                continue
            if identity in missing:
                roots[identity].append(root)
        for model, number in sorted(missing):
            candidates = roots.get((model, number), [])
            if not candidates:
                result["waiting_for_omega"] += 1
                continue
            if len(candidates) != 1:
                result["errors"] += 1
                logger.error(
                    "Несколько корней Omega для %s №%s, импорт пропущен", model, number
                )
                continue
            try:
                incoming = await asyncio.to_thread(
                    client.get_passport_by_root, candidates[0]
                )
                async with async_session_maker() as session:
                    async with session.begin():
                        saved = await add_missing_train_passport(
                            session, model, number, incoming
                        )
                for key, count in saved.items():
                    result[key] += count
                logger.info("Поездной паспорт %s №%s: %s", model, number, saved)
            except Exception:
                result["errors"] += 1
                logger.exception(
                    "Не удалось добавить поездной паспорт %s №%s", model, number
                )
            await asyncio.sleep(settings.OMEGA_SYNC_REQUEST_DELAY_SECONDS)
        return result
