from sqlalchemy import select

from myapp.models.auxiliaries import Supplier
from myapp.train.models.equipment import TrainEquipment
from myapp.utils.equipment_hierarchy import inherited_equipment_value


async def equipment_details(session):
    """Разрешает свойства всех позиций по ближайшему родителю двумя запросами"""
    equipment = {e.id: e for e in (await session.scalars(select(TrainEquipment))).all()}
    suppliers = dict(
        (await session.execute(select(Supplier.id, Supplier.supplier_name))).all()
    )
    result = {}
    for equipment_id, item in equipment.items():
        supplier_id = inherited_equipment_value(equipment_id, equipment, "supplier_id")
        result[equipment_id] = dict(
            name=item.equipment_name,
            parent_id=item.parent_id,
            level=item.level,
            designation=item.designation,
            supplier_id=supplier_id,
            supplier=suppliers.get(supplier_id),
            manufacturer=inherited_equipment_value(
                equipment_id, equipment, "manufacturer"
            ),
        )
    return result
