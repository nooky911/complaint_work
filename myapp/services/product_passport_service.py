from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from myapp.models.auxiliaries import LocomotiveModel
from myapp.models.product_passports import ProductPassport, ProductPassportNode
from myapp.schemas.omega import OmegaPassportData
from myapp.schemas.product_passports import (
    ProductPassportModelResponse,
    ProductPassportNodeResponse,
    ProductPassportResponse,
    ProductPassportSearchItem,
)


class ProductPassportService:
    """Поиск и чтение сохранённых паспортов"""

    @staticmethod
    async def get_models(
        session: AsyncSession,
    ) -> list[ProductPassportModelResponse]:
        """Возвращает модели локомотивов, для которых есть паспорта"""
        statement = (
            select(LocomotiveModel.id, LocomotiveModel.locomotive_model_name)
            .join(ProductPassport)
            .distinct()
            .order_by(LocomotiveModel.locomotive_model_name)
        )
        rows = (await session.execute(statement)).all()
        return [
            ProductPassportModelResponse(id=row.id, name=row.locomotive_model_name)
            for row in rows
        ]

    @staticmethod
    async def search(
        session: AsyncSession,
        locomotive_model_id: int,
        product_number: str,
        limit: int = 20,
    ) -> list[ProductPassportSearchItem]:
        """Ищет паспорта по модели и началу номера локомотива"""
        normalized_number = product_number.strip()
        if not normalized_number:
            return []

        escaped_number = (
            normalized_number.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        statement = (
            select(ProductPassport)
            .where(
                ProductPassport.locomotive_model_id == locomotive_model_id,
                ProductPassport.product_number.ilike(f"{escaped_number}%", escape="\\"),
            )
            .order_by(ProductPassport.product_number)
            .limit(limit)
        )
        passports = (await session.scalars(statement)).all()
        return [
            ProductPassportSearchItem(
                id=passport.id,
                product_number=passport.product_number,
                omega_name=passport.omega_name,
            )
            for passport in passports
        ]

    @staticmethod
    async def get_by_id(
        session: AsyncSession, passport_id: int
    ) -> ProductPassport | None:
        """Возвращает паспорт вместе с моделью и узлами дерева"""
        statement = (
            select(ProductPassport)
            .options(
                joinedload(ProductPassport.locomotive_model),
                selectinload(ProductPassport.nodes),
            )
            .where(ProductPassport.id == passport_id)
        )
        passport = await session.scalar(statement)
        if passport:
            passport.nodes.sort(key=lambda node: (node.level, node.omega_code))
        return passport

    @staticmethod
    def create_model(
        omega_passport: OmegaPassportData,
        product_type: str,
        locomotive_model_id: int,
        product_number: str,
    ) -> ProductPassport:
        """Создаёт модели SQLAlchemy для сохранения паспорта"""
        passport = ProductPassport(
            product_type=product_type,
            locomotive_model_id=locomotive_model_id,
            product_number=product_number,
            omega_root_code=omega_passport.omega_root_code,
            omega_name=omega_passport.omega_name,
        )
        passport.nodes = [
            ProductPassportNode(
                omega_code=node.omega_code,
                parent_omega_code=node.parent_omega_code,
                level=node.level,
                tree_name=node.tree_name,
                full_name=node.full_name,
                peshka=node.peshka,
                designation=node.designation,
                serial_number=node.serial_number,
                manufacture_date=node.manufacture_date,
                install_date=node.install_date,
                manufacturer=node.manufacturer,
                supplier=node.supplier,
                stockobj_code=node.stockobj_code,
            )
            for node in omega_passport.nodes
        ]
        return passport

    @staticmethod
    def to_response(passport: ProductPassport) -> ProductPassportResponse:
        """Убирает технические поля Omega из ответа для интерфейса"""
        node_ids = {node.omega_code: node.id for node in passport.nodes}
        nodes = [
            ProductPassportNodeResponse(
                id=node.id,
                parent_id=node_ids.get(node.parent_omega_code),
                tree_name=node.tree_name,
                full_name=node.full_name,
                peshka=node.peshka,
                designation=node.designation,
                serial_number=node.serial_number,
                manufacture_date=node.manufacture_date,
                install_date=node.install_date,
                manufacturer=node.manufacturer,
                supplier=node.supplier,
            )
            for node in passport.nodes
        ]
        return ProductPassportResponse(
            id=passport.id,
            product_type=passport.product_type,
            locomotive_model_id=passport.locomotive_model_id,
            locomotive_model_name=passport.locomotive_model_name,
            product_number=passport.product_number,
            omega_name=passport.omega_name,
            imported_at=passport.imported_at,
            nodes=nodes,
        )
