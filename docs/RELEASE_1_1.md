# U&I SMART 1.1 - PDF bundles and scanned documents

## Delivered functionality

- Mixed PDF packets stop before extraction under a single document type. Staff review proposed contiguous page ranges in a dialog with an original-page preview. The app rejects overlaps, gaps, incomplete coverage and more than 30 child documents.
- Splitting is transactional: the original PDF is retained, SHA-256 and original page ranges are stored, pending records are extracted into separate child documents. Download the original from each child's source link. Source lineage is included in the seven-sheet workbook and backup/restore.
- Already edited/verified source records cannot be silently discarded by splitting. Staff must use a new case with the original PDF to regroup such a document.
- OCR uses automatic page segmentation rather than treating a full page as a single text block. Simple aligned item/container tables are recovered from OCR word coordinates. Unreadable/missing cells are not invented. This is not a guarantee for arbitrary forms, merged cells or handwriting.
- Bad item row numbers and ambiguous numeric values are flagged. Manual edits recompute warnings instead of retaining stale OCR warnings or trusting client warning flags.
- Opening a case after refreshing reconnects its running job. Cloud OCR allows one case job at a time; completed in-memory job history is bounded.
- Consent to send document contents to OpenAI resets when opening another case or uploading additional files. No automatic AI fallback was added.
- Test PDFs can be downloaded from the Chứng từ panel. Synthetic helpers are collapsed to keep everyday work uncluttered.

## Two matched test files

`samples/fcl-text.pdf` and `samples/fcl-scan.pdf` contain the same fictional shipment. Six pages: Commercial Invoice, Packing List, House B/L, Arrival Notice, Delivery Order, training-only C/O. No real signatures, seals, valid permits or preferential-origin claims.

The second PDF is raster-only, with mild skew, paper tone, scanner streak and compression. There is no hidden text layer. Both files contain clearly visible synthetic-document warnings.

Expected values:

| Value | Expected |
|---|---|
| Invoice | INV-000287-26 |
| B/L | HBL-TEST-261014-009 |
| Invoice amount | 23540.00 USD |
| Invoice items | 2; SKU 00128 and 00456 |
| Quantities | 1200 + 800 = 2000 PCS |
| Packages | 100 cartons |
| Gross / net weight | 5200 / 4910 KG |
| Volume | 21.60 CBM |
| Physical containers | 1; MSCU6639870 / seal MA26101408 / 40HC |

Use a separate case for each PDF. Upload, run Local processing, click Tách bộ PDF, inspect the six page groups and submit. Confirm each type and verify the records against the original pages. Invoice and Packing List each have two item rows; they are four source rows, not four distinct products. A noisy scanned row label may need correction from `=` to `2`; all fields remain pending until staff verification. Do not infer customs clearance from Arrival Notice or Delivery Order.

## Verification and operational limits

Windows release verification: TypeScript/Vite build, 40 Python tests, 8 frontend tests and 2 Node gateway tests passed. Both six-page PDFs were processed, split, individually verified and exported as Reviewed in the isolated synthetic test suite. Fault injection verified transaction rollback. Original-file download, reupload deduplication, review guard, source lineage in Excel, backup inclusion and cloud concurrency guard were checked.

The existing browser UI automation was temporarily unavailable because automatic approval review returned 429. No alternate browser or raw CDP workaround was used. Browser verification and live Linux results are recorded separately when available; successful API/unit tests do not imply visual verification.

This is a functional software upgrade, not a claim of certified production readiness. The current Render Free service still has ephemeral SQLite/files, a shared password, no per-user authorization and no automatic off-site backup. Do not keep the only copy of business records there. A pre-upgrade backup was saved locally outside Git. Persistent cloud storage and employee identities require a separate deployment change; no paid services were created. The local version retains SQLite on the user's disk.

OpenAI connection/model/schema access was proven on the prior release using the user's directly entered key; no customer documents were sent. Memory-only keys can disappear during this deployment. Extraction accuracy on real U&I documents, complex scans and ECUS/VNACCS compatibility remain unproven.
