"""Склады для просмотра документов Omega"""

OMEGA_STOCK_RC_NUMBERS = {
    "receipts": frozenset(
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22)
    ),
    "inplant": frozenset(
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 19, 20, 21, 22)
    ),
    "outbound": frozenset(
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17)
    ),
}

OMEGA_STOCK_WITH_USOE = frozenset(("receipts", "outbound"))
