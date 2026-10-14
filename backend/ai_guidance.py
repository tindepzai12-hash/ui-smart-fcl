"""Synthetic extraction demonstrations; no customer data or evaluation answers."""

EXAMPLES = '''
Synthetic demonstrations only. Never copy their values into the real document.

Example A: page 1 lines:
1 COMMERCIAL INVOICE
2 QUANTITY (PCS) | AMOUNT (EUR)
3 STEEL BOLTS 7.000 12.00 84,000.00
4 TOTAL 84,000.00
Use invoice_total raw_value="84,000.00", source_page=1, evidence_start_line=4,
evidence_end_line=4, unit="EUR", unit_line=2. Separately extract currency="EUR"
with evidence_start_line=2. For the goods row use evidence_start_line=3 and
cell_evidence for unit="PCS" and currency="EUR", each pointing to line 2.
Keep quantity="7.000" literally; do not calculate or change its punctuation.

Example B: page 1 lines:
1 BILL OF LADING
2 Gross weight / Measurement
3 CARTONS 1,234.500
4 KGM
5 16.75 CBM
Use gross_weight raw_value="1,234.500", evidence_start_line=3,
evidence_end_line=3, unit="KGM", unit_line=4. Do not return "1,234.500 KGM"
as raw_value: that string never occurs on one source line/range.
Keep unit/currency null if you cannot locate their printed evidence; an amount
with valid numeric evidence is preferable to losing it by guessing a unit.

Example C: page 1 lines:
1 DELIVERY ORDER
2 Order No: XO17B
3 Voyage: V112
Extract do_number="XO17B" from line 2. Never replace letter O with digit 0.
Extract voyage="V112" from line 3; do not also call it booking.

For the real document, check every evidence pointer against the numbered lines
before submitting. Prefer exact numeric strings from selectable PDF text when
an OCR layer disagrees. Use a separate source line for units, not a reconstructed
quote. Return currency as a standalone field even when also present in items.
'''
