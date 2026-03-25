---
name: boe-to-printable-exit-skill
description: >
  Use this skill when a user uploads a UAE Dubai Customs Bill of Entry (BOE) PDF and wants
  to generate print-ready exit certificates, OR when a user provides shipment details manually
  and wants to fill the Dubai Customs Exit/Entry Certificate. This skill extracts key fields
  from the BOE — including exporter, declaration number and manifest number, date, country of
  origin, port of loading, destination, quantity, goods description, VAT TRN, and weight —
  and produces a complete self-contained 3-page PDF (yellow/green/blue copies) filled via
  embedded form fields, ready to print on plain paper. Also trigger this skill when the user
  wants to correct or update a specific field on a previously generated exit certificate — changes
  apply across all 3 copies automatically. Trigger whenever the user mentions exit certificates,
  customs exit papers, exit papers, شهادة خروج, or asks to process, fill, or correct a BOE.
---

# BOE to Printable Exit Certificates

Generates a filled 3-page Dubai Customs Exit/Entry Certificate PDF from a Bill of Entry (BOE)
or from manually provided data. Uses embedded PDF form fields — no coordinate guessing, always
pixel-perfect regardless of input length.

## Assets

- `assets/exit_papers_template.pdf` — 3-page template (yellow/green/blue) with named form fields
- `scripts/fill_exit_papers.py` — fills all 3 pages in one call

## Workflow

### Mode 1: BOE PDF uploaded

Extract the following fields visually from the BOE. The BOE is a UAE Customs form — sections
are numbered. Extract exactly as shown, stripping any AE-XXXXXXX code prefixes from names.

| Data Field          | BOE Section & Label                              | Notes |
|---------------------|--------------------------------------------------|-------|
| exporter            | Section 6 — IMPORTER / EXPORTER                 | Strip "AE-XXXXXXX - " prefix |
| dec_no              | Section 1 — DEC NO (number inside and outside the box)      | e.g. 201-00007472-26 |
| dec_date            | Section 2 — DEC DATE                            | Format as DD/MM/YYYY |
| country_of_origin   | Section 24 — ORIGIN                             | |
| point_of_exit       | Section 18 — PORT OF LOADING                    | |
| destination         | Section 21 — DESTINATION                        | |
| quantity            | Section 16 — NO. OF PACKAGES                    | |
| description         | Sections 19 + 23 + 12A combined                 | Marks & Numbers + Goods Description + "VAT TRN: XXXXXXXXX" |
| total_weight        | Section 36 — WEIGHT NET                         | Include unit e.g. "102505 KG" |

After extraction, **show the user a summary table** of extracted values and ask them to confirm
or correct before generating. This is important — OCR can miss values on dense forms.

### Mode 2: No BOE — user provides data manually

Ask the user for each field in the table above. Collect all values before generating.

### Mode 3: Correction after generation

The user may say things like "change the destination", "fix the exporter name", or reference
a field by its label on the form. Map their request to the correct data field, update it, and
regenerate. All 3 copies always receive the same data — never update just one page.

**Field name mapping for common user corrections:**

| User says...                        | Data field          |
|-------------------------------------|---------------------|
| exporter / company name             | exporter            |
| bill number / declaration number    | dec_no              |
| manifest number / second number     | manifest_no         |
| date                                | dec_date            |
| country of origin / origin          | country_of_origin   |
| point of exit / port of loading     | point_of_exit       |
| destination / country               | destination         |
| quantity / packages / containers    | quantity            |
| description / goods                 | description         |
| weight / total weight               | total_weight        |

## Generating the PDF

Once all fields are confirmed, run the fill script:

```bash
python /path/to/scripts/fill_exit_papers.py '<json>' /mnt/user-data/outputs/exit_certificates_<dec_no>.pdf
```

Where `<json>` is a single-line JSON string with all 10 fields:

```json
{
  "exporter": "GLOBAL LUBRICANT INDUSTRY LLC",
  "dec_no": "201-00007472-26",
  "manifest_no": "141505260633",
  "dec_date": "06/01/2026",
  "country_of_origin": "AE",
  "point_of_exit": "JEBEL ALI",
  "destination": "BURKINA FASO",
  "quantity": "4 CONTAINER",
  "description": "STC 4X20 STD 5395 PACKAGES AS PER INVOICE NUMBER 0013098\nLUBRIMAX GOLD GEAR OIL\nVAT TRN: 100360009300003",
  "total_weight": "102505 KG"
}
```

After running, present the output file to the user with `present_files`.

## Text fitting rules

The script handles font sizing automatically per field. Description and BillNo fields are
multiline. However, if the user notices overflow on a specific field, reduce verbosity of
that field's value (e.g. abbreviate description lines) and regenerate — do not truncate
silently without telling the user.

## Important notes

- **ExportBillNoFormField is intentionally left blank** — do not fill it
- **ContainerNoFormField is intentionally left blank** — do not fill it
- All 3 pages always receive identical data — never fill pages selectively
- The template PDF path is relative to the script: `../assets/exit_papers_template.pdf`
- Output filename should include the DEC NO for traceability