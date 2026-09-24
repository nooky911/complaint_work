"""SQL-запросы только для чтения паспортов из Oracle Omega"""

LIST_ROOT_PASSPORTS_SQL = """
SELECT q.CODE, q.NAME
FROM OMP_ADM.QUALITY_CONTROL_DOCUMENT q
WHERE REGEXP_LIKE(
    q.NAME,
    '^Электровоз[[:space:]]+[^[:space:]]+[[:space:]]+№[[:space:]]*[^[:space:]()]+([[:space:]]*[(][^)]*[)])?$',
    'i'
)
  AND EXISTS (
      SELECT 1
      FROM OMP_ADM.OMP_OBJECT_CONTENTS child_link
      WHERE child_link.CONTCODE = q.CODE
        AND child_link.DELETEDATE IS NULL
  )
  AND NOT EXISTS (
      SELECT 1
      FROM OMP_ADM.OMP_OBJECT_CONTENTS parent_link
      JOIN OMP_ADM.QUALITY_CONTROL_DOCUMENT parent_q
        ON parent_q.CODE = parent_link.CONTCODE
       AND parent_q.PRODCOPY_CODE = q.PRODCOPY_CODE
      WHERE parent_link.ITEMCODE = q.CODE
        AND parent_link.DELETEDATE IS NULL
  )
ORDER BY q.CODE
"""


PASSPORT_TREE_SQL = """
SELECT
    tree.lvl,
    tree.parent_code,
    tree.code,
    q.NAME AS tree_name,
    s.SIGN AS peshka,
    a.A_13404 AS full_name,
    a.A_13405 AS designation,
    a.A_13415 AS serial_number,
    a.A_13393 AS manufacture_date,
    a.A_13394 AS install_date,
    a.A_13399 AS manufacturer,
    supplier.SHORTNAME AS supplier,
    q.STOCKOBJ_CODE
FROM (
    SELECT 0 AS lvl, CAST(NULL AS NUMBER) AS parent_code, :root_code AS code
    FROM dual
    UNION ALL
    SELECT LEVEL AS lvl, c.CONTCODE AS parent_code, c.ITEMCODE AS code
    FROM (
        SELECT DISTINCT CONTCODE, ITEMCODE
        FROM OMP_ADM.OMP_OBJECT_CONTENTS
        WHERE DELETEDATE IS NULL
          -- В паспорте 2ЭС6 №1541 ветка секции Б ошибочно привязана к секции А
          AND NOT (CONTCODE = 2169773713 AND ITEMCODE = 2169116031)
    ) c
    START WITH c.CONTCODE = :root_code
    CONNECT BY NOCYCLE PRIOR c.ITEMCODE = c.CONTCODE
) tree
LEFT JOIN OMP_ADM.QUALITY_CONTROL_DOCUMENT q
  ON q.CODE = tree.code
LEFT JOIN OMP_ADM.OBJ_ATTR_VALUES_425 a
  ON a.SOCODE = tree.code
LEFT JOIN OMP_ADM.STOCKOBJ s
  ON s.CODE = q.STOCKOBJ_CODE
LEFT JOIN OMP_ADM.ENTERPRISE supplier
  ON supplier.SOCODE = CASE
      WHEN REGEXP_LIKE(a.A_13407, '^[0-9]+$') THEN TO_NUMBER(a.A_13407)
     END
WHERE tree.code = :root_code OR q.CODE IS NOT NULL
ORDER BY tree.lvl, tree.parent_code, tree.code
"""
