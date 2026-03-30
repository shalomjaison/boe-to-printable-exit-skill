---
name: boe-to-printable-exit-skill
description: >
  Use this skill when a user uploads a UAE Dubai Customs Bill of Entry (BOE) PDF and wants
  to generate print-ready exit certificates, OR when a user provides shipment details manually
  and wants to fill the Dubai Customs Exit/Entry Certificate. This skill extracts key fields
  from the BOE — including exporter, both the declaration numbers, date, country of
  origin, port of loading, destination, quantity, goods description, VAT TRN, and weight —
  and produces a single-page filled PDF via embedded form fields, ready to print onto 3 physical 
  colored paper copies (yellow/green/blue). Also trigger this skill when the user wants to correct 
  or update a specific field on a previously generated exit certificate. Trigger whenever the user 
  mentions exit certificates, customs exit papers, exit papers, شهادة خروج, or asks to process, 
  fill, or correct a BOE.
---

# BOE to Printable Exit Certificates

Generates a filled single-page Dubai Customs Exit/Entry Certificate PDF from a Bill of Entry (BOE) or from manually provided data. The single page is designed to be printed 3 times onto physical yellow, green, and blue paper copies. Uses embedded PDF form fields — no coordinate guessing, always pixel-perfect regardless of input length.

## Assets

- `assets/exit_papers_template_patched.pdf` — single-page layout template with named form fields and pre-patched
- `scripts/fill_exit_papers.py` — fills the page layout template in one call
- `scripts/patch_once.py` — re-patches the template if AcroForm compatibility is ever broken and also has functions to remove text box borders and content stream from a template pdf

Look for the template first in `assets/exit_papers_template_patched.pdf` (relative to this SKILL.md).
If not found there, check if the user has uploaded it directly in chat.

## Template Patching

The template PDF (`assets/exit_papers_template_patched.pdf`) has already been **pre-patched** for
AcroForm compatibility. **Do not re-patch it as part of normal operation.**

The template has a transparent/white background by design — this is intentional
so that text-only data prints onto the physical colored papers. A blank-looking
template is correct behaviour, not a sign of corruption.

If form fields fail to fill or save correctly (e.g. fields appear blank in the output PDF
after running the fill script), re-patching may be needed. A patch script is available
in the scripts directory:

```bash
python <skill_dir>/scripts/patch_once.py
```

This regenerates the patched template in-place. **Only run this if the fill script produces
a PDF with empty fields** — not as a routine step.

## Workflow

### Mode 1: BOE PDF uploaded

Extract the following fields visually from the BOE. The BOE is a UAE Customs form — sections
are numbered. Extract exactly as shown, stripping any AE-XXXXXXX code prefixes from names.
The BOE PDF will either be uploaded directly in chat, or found in the mounted uploads folder.
Check both before asking the user to upload it.

| Data Field        | BOE Section & Label                              | Notes |
|-------------------|--------------------------------------------------|-------|
| exporter          | Section 6 — IMPORTER / EXPORTER                 | Strip "AE-XXXXXXX - " prefix |
| dec_no_part1      | Section 1 — DEC NO (number inside the box)      | e.g. 201-00007472-26 |
| dec_no_part2      | Section 1 — number printed below the DEC NO box | e.g. 141505260633 |
| dec_date          | Section 2 — DEC DATE                            | Format as DD/MM/YYYY |
| country_of_origin | Section 24 — ORIGIN                             | |
| point_of_exit     | Section 18 — PORT OF LOADING                    | |
| destination       | Section 21 — DESTINATION                        | |
| quantity          | Section 16 — NO. OF PACKAGES                    | |
| description       | Sections 19 + 23 + 12A combined                 | Marks & Numbers + Goods Description + "VAT TRN: XXXXXXXXX" — see example JSON below |
| total_weight      | Section 36 — WEIGHT NET                         | Include unit e.g. "102505 KG" |

After extraction, **show the user a summary table** of extracted values and ask them to confirm
or correct before generating. This is important — OCR can miss values on dense forms.

### Mode 2: No BOE — user provides data manually

Ask the user for each field in the table above. Collect all values before generating.

### Mode 3: Correction, addition, or removal after generation

The user may say things like "change the destination", "fix the exporter name", or reference
a field by its label on the form. Map their request to the correct data field, update it, and
regenerate.

The user may also ask to fill fields that were left blank by default. The following fields are
optional and only filled on request:

| Field name (PDF)         | Label on form   |
|--------------------------|-----------------|
| ManifestNoFormField      | Air way bill no / Export Bill No / Manifest No     |
| CustomsSealNoFormField   | Customs Seal No |
| ContainerNoFormField     | Container No / Vehicle No   |

The user may also ask to clear a field that was previously filled — set its value to `""` and
regenerate.

**Field name mapping for common user corrections:**

| User says...                        | Data field                  |
|-------------------------------------|-----------------------------|
| exporter / company name             | exporter                    |
| bill number / declaration number    | dec_no_part1 + dec_no_part2 |
| second number                       | dec_no_part2                |
| date                                | dec_date                    |
| country of origin / origin          | country_of_origin           |
| point of exit / port of loading     | point_of_exit               |
| destination / country               | destination                 |
| quantity / packages / containers    | quantity                    |
| description / goods                 | description                 |
| weight / total weight               | total_weight                |
| manifest no / Air Way Bill No / Export Bill No| ManifestNoFormField         |
| customs seal no                     | CustomsSealNoFormField      |
| container no / vehicle no           | ContainerNoFormField        |
| remove / clear / delete [field]     | Set that field to ""        |


## Generating the PDF

Once all fields are confirmed, run the fill script using the path relative to this SKILL.md:

```bash
python <skill_dir>/scripts/fill_exit_papers.py '<json>' /mnt/user-data/outputs/exit_certificates_<dec_no_part1>.pdf
```

Where `<skill_dir>` is the directory containing this SKILL.md, and `<json>` is a single-line
JSON string with the required fields.

**Example only — replace with actual extracted values:**
```json
{
  "exporter": "GLOBAL LUBRICANT INDUSTRY LLC",
  "dec_no_part1": "201-00007472-26",
  "dec_no_part2": "141505260633",
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

## Text Fitting Rules

The script handles font sizing automatically per field. Description and BillNo fields are
multiline. However, if the user notices overflow on a specific field, reduce verbosity of
that field's value (e.g. abbreviate description lines) and regenerate — do not truncate
silently without telling the user.

## Important Notes
- The template path used by the fill script is relative to the script: `../assets/exit_papers_template_patched.pdf`
- Output filename should include the DEC NO for traceability
