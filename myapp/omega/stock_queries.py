"""Запросы для просмотра складских документов Omega"""

WAREHOUSES_SQL = """
SELECT CODE, SIGN, NAME
FROM OMP_ADM.DIVISIONOBJ
WHERE DIVISION_TYPE = 105
ORDER BY SIGN
"""

DOCUMENT_QUERIES = {
    "receipts": """
        SELECT o.CODE AS DOCUMENT_ID, o.ORDNUM AS NUMBER,
               o.SUPPLDOCDATE AS ACCOMPANYING_DATE,
               w.SIGN || ' - ' || w.NAME AS WAREHOUSE,
               e.NAME AS SUPPLIER, o.SUPPLDOCNUM AS ACCOMPANYING_NUMBER,
               o.ORDDATE AS ACCOUNTING_DATE, o.NOTICE AS NOTE,
               b.CREATE_DATE AS CREATED_AT, creator.FULLNAME AS CREATED_BY,
               b.UPDATE_DATE AS UPDATED_AT
        FROM OMP_ADM.STOCK_ORDER o
        JOIN OMP_ADM.DIVISIONOBJ w ON w.CODE = o.WSCODE
        LEFT JOIN OMP_ADM.ENTERPRISE e ON e.ENTCODE = o.SUPPLYENT
        LEFT JOIN OMP_ADM.BUSINESS_OBJECTS b ON b.CODE = o.CODE
        LEFT JOIN OMP_ADM.USER_LIST creator ON creator.CODE = b.CREATE_USER
        WHERE NVL(o.ISDELETED, 0) = 0
          AND o.WSCODE IN ({warehouses})
          {filters}
        ORDER BY o.ORDDATE DESC, o.CODE DESC
        OFFSET :p_offset ROWS FETCH NEXT :p_limit ROWS ONLY
    """,
    "inplant": """
        SELECT i.CODE AS DOCUMENT_ID, i.INVOICEDATE AS DOCUMENT_DATE,
               CASE WHEN i.ACCEPT_DATE IS NOT NULL THEN 'Принят'
                    WHEN i.CONFIRMED = 1 THEN 'Выдано'
                    ELSE 'Не утвержден' END AS STATUS,
               i.INVOICENUM AS NUMBER, i.NOTICE AS NOTE,
               sender.SIGN || ' - ' || sender.NAME AS WAREHOUSE,
               accepted.FULLNAME AS ACCEPTED_BY,
               receiver.SIGN || ' - ' || receiver.NAME AS RECIPIENT,
               issued.FULLNAME AS ISSUED_BY
        FROM OMP_ADM.STOCK_INPLANT_INVOICE i
        JOIN OMP_ADM.DIVISIONOBJ sender ON sender.CODE = i.WSSENDERCODE
        LEFT JOIN OMP_ADM.DIVISIONOBJ receiver ON receiver.CODE = i.WSADDRESSECODE
        LEFT JOIN OMP_ADM.USER_LIST accepted ON accepted.CODE = i.CONFIRM_ID
        LEFT JOIN OMP_ADM.USER_LIST issued ON issued.CODE = i.SENDERCODE
        WHERE NVL(i.ISDELETED, 0) = 0
          AND i.WSSENDERCODE IN ({warehouses})
          AND receiver.SIGN = 'РЕК_УСОЭ'
          {filters}
        ORDER BY i.INVOICEDATE DESC, i.CODE DESC
        OFFSET :p_offset ROWS FETCH NEXT :p_limit ROWS ONLY
    """,
    "outbound": """
        SELECT i.CODE AS DOCUMENT_ID, i.INVOICENUM AS NUMBER,
               w.SIGN || ' - ' || w.NAME AS WAREHOUSE,
               e.NAME AS RECIPIENT, i.INVOICEDATE AS DOCUMENT_DATE,
               i.SHIPPING_DATE,
               CASE WHEN i.CONFIRMED = 1 THEN 'Утв' ELSE 'Неутв' END AS STATUS,
               b.CREATE_DATE AS CREATED_AT,
               CASE WHEN EXISTS (
                   SELECT 1 FROM OMP_ADM.ATTACHMENTS a
                   WHERE a.BUSINESSOBJ = i.CODE
               ) THEN 1 ELSE 0 END AS HAS_FILES,
               creator.FULLNAME AS CREATED_BY,
               b.UPDATE_DATE AS UPDATED_AT,
               editor.FULLNAME AS UPDATED_BY
        FROM OMP_ADM.STOCK_ONSIDE_INVOICE i
        JOIN OMP_ADM.DIVISIONOBJ w ON w.CODE = i.WSSENDERCODE
        LEFT JOIN OMP_ADM.ENTERPRISE e ON e.ENTCODE = i.ENTCODE
        LEFT JOIN OMP_ADM.BUSINESS_OBJECTS b ON b.CODE = i.CODE
        LEFT JOIN OMP_ADM.USER_LIST creator ON creator.CODE = b.CREATE_USER
        LEFT JOIN OMP_ADM.USER_LIST editor ON editor.CODE = b.UPDATE_USER
        WHERE NVL(i.ISDELETED, 0) = 0
          AND i.WSSENDERCODE IN ({warehouses})
          {filters}
        ORDER BY i.INVOICEDATE DESC, i.CODE DESC
        OFFSET :p_offset ROWS FETCH NEXT :p_limit ROWS ONLY
    """,
}

DETAIL_QUERIES = {
    "receipts": """
        SELECT p.CODE AS ITEM_ID, lot.CODE AS LOT_MOVEMENT_ID,
               p.NUM_POS AS POSITION,
               d.DEPOTCARDNUM AS CARD_NUMBER,
               s.DESCRIPTION AS NOMENCLATURE, s.NOMSIGN AS NOMINAL_NUMBER,
               p.DOCQUANTITY AS DOCUMENT_QUANTITY,
               p.FACTQUANTITY AS QUANTITY, m.SHORTNAME AS UNIT,
               p.PRICE_MC AS PRICE_RUB, p.NDS AS VAT_RUB,
               p.SUM_SUPP_WITH_NDS AS TOTAL_WITH_VAT,
               d.DEPOTCARDNUM AS DEPOT_CARD,
               party.NUM AS PARTY_NUMBER
        FROM OMP_ADM.STOCK_ORDER_ITEMS p
        LEFT JOIN OMP_ADM.STOCKOBJ s ON s.CODE = p.STOCKOBJCODE
        LEFT JOIN OMP_ADM.MEASURES m ON m.CODE = p.MEASCODE
        LEFT JOIN OMP_ADM.STOCK_DEPOTCARD d ON d.CODE = p.DEPOTCODE
        LEFT JOIN OMP_ADM.LOT_STOCK_DOCUMENT_BODY lot
               ON lot.DOC_CODE = p.ORDERCODE
              AND lot.BASE_CODE = p.CODE
        LEFT JOIN OMP_ADM.OMP_OBJECTS party
               ON party.CODE = lot.LOT_SO_NUM_CODE
        WHERE p.ORDERCODE = :p_document_id
        ORDER BY p.NUM_POS, p.CODE, lot.CODE
    """,
    "inplant": """
        SELECT p.CODE AS ITEM_ID, source_lot.CODE AS LOT_MOVEMENT_ID,
               s.NOMSIGN AS NOMINAL_NUMBER,
               d.DEPOTCARDNUM AS SENDER_CARD,
               d_receiver.DEPOTCARDNUM AS RECEIVER_CARD,
               s.DESCRIPTION AS NOMENCLATURE,
               p.QUANTITY, m.SHORTNAME AS UNIT,
               COALESCE(p.NOTICE, d_receiver.NOTICE) AS ITEM_NOTE,
               i.INVOICENUM AS INVOICE_NUMBER,
               i.INVOICEDATE AS INVOICE_DATE,
               sender.NAME AS SENDER_WAREHOUSE,
               sender.SIGN AS SENDER_SIGN,
               lot_number.NUM AS LOT_MOVEMENT_NUMBER,
               parent_number.NUM AS PARENT_LOT_MOVEMENT_NUMBER,
               source_lot.LOT_DOC_NUM AS ORIGINAL_DOCUMENT_NUMBER
        FROM OMP_ADM.STOCK_BODY_INPLANT_INVOICE p
        JOIN OMP_ADM.STOCK_INPLANT_INVOICE i ON i.CODE = p.INVOICECODE
        LEFT JOIN OMP_ADM.DIVISIONOBJ sender ON sender.CODE = i.WSSENDERCODE
        LEFT JOIN OMP_ADM.STOCKOBJ s ON s.CODE = p.STOCKOBJCODE
        LEFT JOIN OMP_ADM.MEASURES m ON m.CODE = p.MEASCODE
        LEFT JOIN OMP_ADM.STOCK_DEPOTCARD d ON d.CODE = p.DEPOTCODE
        LEFT JOIN OMP_ADM.STOCK_DEPOTCARD d_receiver
               ON d_receiver.CODE = (
                   SELECT MAX(card.CODE)
                   FROM OMP_ADM.STOCK_DEPOTCARD card
                   WHERE card.STOCKOBJCODE = p.STOCKOBJCODE
                     AND card.WSCODE = i.WSADDRESSECODE
                   HAVING COUNT(*) = 1
               )
        LEFT JOIN OMP_ADM.LOT_STOCK_DOCUMENT_BODY source_lot
               ON source_lot.DOC_CODE = p.INVOICECODE
              AND source_lot.BASE_CODE = p.CODE
              AND source_lot.LOT_DOC_CODE <> p.INVOICECODE
        LEFT JOIN OMP_ADM.OMP_OBJECTS lot_number
               ON lot_number.CODE = source_lot.LOT_SO_NUM_CODE
        LEFT JOIN OMP_ADM.LOT_STOCK_DOCUMENT_BODY parent_lot
               ON parent_lot.CODE = source_lot.PARENT_LOT_CODE
        LEFT JOIN OMP_ADM.OMP_OBJECTS parent_number
               ON parent_number.CODE = parent_lot.SO_NUM_CODE
        WHERE p.INVOICECODE = :p_document_id
        ORDER BY p.CODE, source_lot.CODE
    """,
    "outbound": """
        SELECT p.CODE AS ITEM_ID, source_lot.CODE AS LOT_MOVEMENT_ID,
               d.DEPOTCARDNUM AS CARD_NUMBER,
               s.DESCRIPTION AS NOMENCLATURE, s.NOMSIGN AS NOMINAL_NUMBER,
               p.QUANTITY, m.SHORTNAME AS UNIT,
               d.DEPOTCARDNUM AS DEPOT_CARD,
               party.NUM AS PARTY_NUMBER,
               CASE WHEN source_doc.TYPE = 1024 THEN 'ПО' END
                   AS ORIGIN_DOCUMENT_TYPE,
               source_lot.LOT_DOC_NUM AS ORIGINAL_DOCUMENT_NUMBER,
               source_lot.LOT_DOC_DATE AS ORIGIN_DOCUMENT_DATE
        FROM OMP_ADM.STOCK_BODY_ONSIDE_INVOICE p
        LEFT JOIN OMP_ADM.STOCK_DEPOTCARD d ON d.CODE = p.DEPOTCODE
        LEFT JOIN OMP_ADM.STOCKOBJ s ON s.CODE = d.STOCKOBJCODE
        LEFT JOIN OMP_ADM.MEASURES m ON m.CODE = d.MEASCODE
        LEFT JOIN OMP_ADM.LOT_STOCK_DOCUMENT_BODY source_lot
               ON source_lot.DOC_CODE = p.INVOICECODE
              AND source_lot.BASE_CODE = p.CODE
              AND source_lot.LOT_DOC_CODE <> p.INVOICECODE
        LEFT JOIN OMP_ADM.OMP_OBJECTS party
               ON party.CODE = source_lot.LOT_SO_NUM_CODE
        LEFT JOIN OMP_ADM.STOCK_DOCUMENTS source_doc
               ON source_doc.CODE = source_lot.LOT_DOC_CODE
        WHERE p.INVOICECODE = :p_document_id
        ORDER BY p.CODE, source_lot.CODE
    """,
}

DOCUMENT_TABLES = {
    "receipts": "STOCK_ORDER",
    "inplant": "STOCK_INPLANT_INVOICE",
    "outbound": "STOCK_ONSIDE_INVOICE",
}

FILES_SQL = """
SELECT DISTINCT a.DOCUMENT AS ID,
       'Вложение ' || TO_CHAR(a.DOCUMENT) AS NAME
FROM OMP_ADM.ATTACHMENTS a
WHERE a.BUSINESSOBJ = :p_document_id
ORDER BY ID
"""

FILE_EXISTS_SQL = """
SELECT 1
FROM OMP_ADM.ATTACHMENTS a
WHERE a.BUSINESSOBJ = :p_document_id
  AND a.DOCUMENT = :p_file_id
FETCH FIRST 1 ROWS ONLY
"""

FILE_PARTS_SQL = """
SELECT NUM, COMPRESSED, DATA
FROM OMP_ADM.DOCUMENTS_PARTS
WHERE CODE = :p_file_id
ORDER BY NUM
"""
