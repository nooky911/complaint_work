from sqlalchemy import or_, func, String


def apply_filter_conditions(conditions: list, fields_mapping: list, empty_fields=()):
    """Добавляет общие условия мультивыбора и незаполненных значений"""
    for p_val, col in fields_mapping:
        alternatives = []
        if col.key in empty_fields and col.nullable:
            empty_condition = col.is_(None)
            if isinstance(col.type, String):
                empty_condition = or_(empty_condition, func.trim(col) == "")
            alternatives.append(empty_condition)

        if isinstance(p_val, list):
            clean_list = [v for v in p_val if v is not None and str(v).strip() != ""]
            if clean_list:
                alternatives.append(col.in_(clean_list))
        elif p_val is not None:
            val_str = str(p_val).strip()
            if val_str != "" and val_str.lower() != "none":
                alternatives.append(col == p_val)

        if alternatives:
            conditions.append(or_(*alternatives))
