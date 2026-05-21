---
name: boe-to-printable-exit-skill
description: >
  Use this skill when a user uploads a UAE Bill of Entry (BOE) PDF from either Dubai Customs or Sharjah Ports, Customs and Free Zone Authority, and wants to generate print-ready exit certificates. Also use when the user provides shipment details manually. This skill detects the issuing authority from the BOE header, extracts the relevant fields, and produces a filled single-page PDF via embedded form fields, ready to print onto 3 physical colored paper copies (yellow/green/blue). Also trigger when the user wants to correct or update a field on a previously generated exit certificate. Trigger whenever the user mentions exit certificates, customs exit papers, exit papers, Sharjah exit, Dubai exit, شهادة خروج, or asks to process, fill, or correct a BOE.
---

# BOE to Printable Exit Certificates

Generates a filled single-page Dubai Customs Exit/Entry Certificate PDF from a Bill of Entry (BOE) or from manually provided data. The single page is designed to be printed 3 times onto physical yellow, green, and blue paper copies. Uses embedded PDF form fields — no coordinate guessing, always pixel-perfect regardless of input length.

## Assets

| File | Purpose |
|------|---------|
| `assets/dubai_exit_template_patched.pdf` | Dubai exit certificate template (pre-patched, use this normally) |
| `assets/sharjah_exit_template_patched.pdf` | Sharjah exit certificate template (pre-patched, use this normally) |
| `assets/DubaiCustomsExitFormFields.pdf` | Dubai unpatched source template (use only if re-patching) |
| `assets/SharjahCustomsExitFormFields.pdf` | Sharjah unpatched source template (use only if re-patching) |
| `scripts/fill_exit_papers.py` | Fills whichever template is passed to it in one call|
| `scripts/patch_once.py` | Re-patches a template if AcroForm compatibility breaks and also has functions to remove text box borders and content stream from a template pdf. Pass `dubai` or `sharjah` as argument |

Look for the template first in `assets/dubai_exit_template_patched.pdf` `assets/sharjah_exit_template_patched.pdf` (relative to this SKILL.md).
If not found there, check if the user has uploaded it directly in chat.

## Template Patching

Both template PDF's have already been **pre-patched** for
AcroForm compatibility. **Do not re-patch it as part of normal operation.**

The template has a transparent/white background by design — this is intentional
so that text-only data prints onto the physical colored papers. A blank-looking
template is correct behaviour, not a sign of corruption.

If form fields fail to fill or save correctly (e.g. fields appear blank in the output PDF
after running the fill script), re-patching may be needed. A patch script is available
in the scripts directory:

```bash
python <skill_dir>/scripts/patch_once.py dubai
# or
python <skill_dir>/scripts/patch_once.py sharjah
```

This regenerates the patched template in-place. **Only run this if the fill script produces
a PDF with empty fields** — not as a routine step.

## Workflow

### Step 1 — Detect Authority

Read the BOE header (top of first page):

| Header text | Authority |
|-------------|-----------|
| Contains "Dubai Customs" | → Dubai branch |
| Contains "Sharjah Ports, Customs and Free Zone Authority" | → Sharjah branch |
| Unclear | → Ask the user: "Is this a Dubai Customs or Sharjah Customs BOE?" |

All subsequent steps branch on this result.

### Step 1b — Choose Exit Certificate Type
 
After detecting the BOE authority, ask the user which exit certificate to generate:
 
> "Which exit certificate should I generate — Dubai or Sharjah?"
 
This is independent of the BOE source. A Dubai BOE can produce a Sharjah exit certificate and vice versa (cross-filling). Use the selected certificate type to determine which template to fill, but always extract data using the BOE authority's extraction table (Step 1 / Mode 1).
 
| BOE Authority | Certificate Type | Template used |
|---------------|-----------------|---------------|
| Dubai         | Dubai           | `dubai_exit_template_patched.pdf` |
| Dubai         | Sharjah         | `sharjah_exit_template_patched.pdf` |
| Sharjah       | Sharjah         | `sharjah_exit_template_patched.pdf` |
| Sharjah       | Dubai           | `dubai_exit_template_patched.pdf` |
 
**Cross-fill field mapping notes:**
- When filling a Sharjah certificate from a Dubai BOE: `dec_no` = `dec_no_part1` (use the first part only); `container_no` = value from Dubai Section 18 if available, otherwise leave blank; `total_value` and `currency` are not on Dubai BOEs — ask the user if they want to fill these, otherwise leave blank.
- When filling a Dubai certificate from a Sharjah BOE: `dec_no_part1` = `dec_no`; `dec_no_part2` = leave blank (`""`); `AirwayBillReferenceNoFormField` = not applicable, leave blank.

### Mode 1: BOE PDF uploaded

The BOE PDF will either be uploaded directly in chat, or found in the mounted uploads folder.
Check both before asking the user to upload it. Extract exactly as shown per authority.

#### Dubai BOE

Strip any AE-XXXXXXX code prefixes from the exporter name.

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
| description       | Sections 19 + 23 + 12A combined                 | Marks & Numbers + Goods Description + "VAT TRN: XXXXXXXXX" |
| total_weight      | Section 36 — WEIGHT NET                         | Include unit e.g. "102505 KG" |


#### Sharjah BOE

| Data Field        | BOE Section & Label                              | Notes |
|-------------------|--------------------------------------------------|-------|
| exporter          | Section 6 — CONSIGNEE / EXPORTER                | |
| dec_no            | Section 1 — DEC NO                              | Single number, no part2 |
| dec_date          | Section 2 — DEC DATE                            | Format as DD/MM/YYYY |
| country_of_origin | Section 24 — COUNTRY OF ORIGIN column           | Per line item — take unique values, comma-separated |
| point_of_exit     | Section 51 — EXIT PORT                          | |
| destination       | Section 21 — DESTINATION                        | |
| quantity          | Section 16 — NO. OF PACKAGES                    | Total quantity for the certificate |
| description       | Sections 22–44 line items table                 | Col 23 for description, col 32 or 34 for qty per row — see below |
| total_weight      | Section 10 — GROSS WEIGHT                       | Include unit e.g. "5200 KG" |
| container_no      | Section 19 — MARKS & NUMBERS                    | |
| vat_trn           | Not on BOE                                      | Ask user before generating |
| total_value       | Column 28 — CIF LOCAL VALUE                     | Sum across all pages. Include currency prefix in output e.g. "AED 125000.00" |
| currency          | Column 28 header                                | Usually AED — extract if shown, default to AED |


After extraction, **show the user a summary table** of extracted values and ask them to confirm
or correct before generating. This is important — OCR can miss values on dense forms.

For Sharjah: 
- If VAT TRN has not yet been provided, ask for it at this step before proceeding.
- When reading the BOE, Column 28 (CIF Local Value) appears per line item across multiple pages. Claude needs to:
  1. Extract all numeric values from column 28
  2. Sum them
  3. Format as {currency} {total} — e.g. AED 247500.00
  4. Pass currency and total_value as separate keys to the script

Also include the optional fields in the summary, shown as empty, so the user knows which fields
are available and what keyword to say to fill them:

**Dubai optional fields:**

| Field | Value | Say this to fill it |
|-------|-------|---------------------|
| Export Bill No / Manifest No | *(not filled)* | "manifest no" |
| Customs Seal No | *(not filled)* | "customs seal no" |
| Container No / Vehicle No | *(not filled)* | "container no" |
| Airway Bill Reference No | *(not filled)* | "reference no" |
| Date of Execution | *(not filled)* | "date of execution" |

**Sharjah optional fields:**

| Field | Value | Say this to fill it |
|-------|-------|---------------------|
| Manifest Bill No | *(not filled)* | "manifest no" |
| Customs Seal No | *(not filled)* | "customs seal no" |
| Date of Execution | *(not filled)* | "date of execution" |

### Mode 2: No BOE — user provides data manually

Ask the user which authority (Dubai or Sharjah), then ask for each field in the corresponding
extraction table above. Collect all values before generating.

### Mode 3: Correction, addition, or removal after generation

The user may say things like "change the destination", "fix the exporter name", or reference
a field by its label on the form. Map their request to the correct data field, update it, and
regenerate using the same authority branch.

The user may also ask to fill fields that were left blank by default. The following fields are
optional and only filled on request:

| Field name (PDF)         | Label on form   |
|--------------------------|-----------------|
| ManifestNoFormField      | Export Bill No / Manifest No     |
| CustomsSealNoFormField   | Customs Seal No |
| ContainerNoFormField     | Container No / Vehicle No   |
| AirwayBillReferenceNoFormField | Airway Bill Reference Number |
| ExecutionDateFormField   | Date of Execution |

The user may also ask to clear a field that was previously filled — set its value to `""` and
regenerate.

**Dubai field mapping:**

| User says... | Data field |
|---|---|
| exporter / company name | exporter |
| bill number / declaration number | dec_no_part1 + dec_no_part2 |
| second number | dec_no_part2 |
| date | dec_date |
| country of origin / origin | country_of_origin |
| point of exit / port of loading | point_of_exit |
| destination / country | destination |
| quantity / packages / containers | quantity |
| description / goods | description |
| weight / total weight | total_weight |
| manifest no / Air Way Bill No / Export Bill No | ManifestNoFormField |
| customs seal no | CustomsSealNoFormField |
| container no / vehicle no | ContainerNoFormField |
| airway bill reference no / reference no | AirwayBillReferenceNoFormField |
| date of execution | ExecutionDateFormField |
| remove / clear / delete [field] | Set that field to "" |

**Sharjah field mapping:**

| User says... | Data field |
|---|---|
| exporter / company name | exporter |
| bill number / declaration number | dec_no |
| date | dec_date |
| country of origin / origin | country_of_origin |
| point of exit / exit port | point_of_exit |
| destination / country | destination |
| quantity / packages | quantity |
| description / goods / line items | description |
| weight / total weight | total_weight |
| container no / marks & numbers | container_no |
| VAT TRN | Append/update TRN line at end of description |
| manifest bill no | ManifestNoFormField |
| customs seal no | CustomsSealNoFormField |
| date of execution | ExecutionDateFormField |
| value / total value / CIF value | total_value |
| currency | currency |
| remove / clear / delete [field] | Set that field to "" |


## Generating the PDF

Once all fields are confirmed, run the fill script. `<skill_dir>` is the directory containing this SKILL.md.

The template to pass is determined by the **certificate type chosen in Step 1b**, not the BOE authority. Dubai certificate = no third argument (uses default). Sharjah certificate = pass the Sharjah template path explicitly.

**Dubai:**
```bash
python <skill_dir>/scripts/fill_exit_papers.py '<json>' /mnt/user-data/outputs/exit_certificates_<dec_no_part1>.pdf
```

**Sharjah:**
```bash
python <skill_dir>/scripts/fill_exit_papers.py '<json>' /mnt/user-data/outputs/exit_certificates_<dec_no>.pdf <skill_dir>/assets/sharjah_exit_template_patched.pdf
```

**Dubai example JSON:**
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

**Sharjah example JSON:**
```json
{
  "exporter": "ARABIAN EXPORTS LLC",
  "dec_no": "SHJ-00012345-26",
  "dec_date": "10/05/2026",
  "country_of_origin": "AE, CN",
  "point_of_exit": "SHARJAH PORT",
  "destination": "KENYA",
  "quantity": "120 CARTONS",
  "description": "PLASTIC PIPES 50MM x 120\nSTEEL RODS 6MM x 80\nVAT TRN: 100512009400001",
  "total_weight": "5200 KG",
  "container_no": "MSKU1234567",
  "currency": "AED",
  "total_value": "125000.00"
}
```

After running, present the output file to the user with `present_files`.

## Text Fitting Rules

The script handles font sizing automatically per field. Description and BillNo fields are
multiline. Font sizes are baked into the template at patch time via patch_once.py.

If the user notices overflow on a specific field, ask them which field looks wrong, then
re-run the fill script with a lower font size override for that field by passing a
`font_overrides` key in the JSON — e.g.:

  "font_overrides": { "ExporterFormField": 7 }

Note: font_overrides support is not yet implemented in fill_exit_papers.py. Until it is,
reduce the font size in DUBAI_CUSTOMS_FONT_SIZES or SHARJAH_CUSTOMS_FONT_SIZES in
patch_once.py and re-patch the template.


## Important Notes
- Dubai default template: `../assets/dubai_exit_template_patched.pdf` (relative to the fill script)
- Sharjah template must be passed explicitly as the third argument to the fill script
- Output filename should include the DEC NO for traceability
- Field borders and white background fills are handled in two places:
  (1) `patch_once.py` removes white box backgrounds (`MK/BG`) and border color (`MK/BC`)
  from the template permanently — both assets are already patched. Run with `dubai` or `sharjah` argument if re-patching is needed.
  (2) `fill_exit_papers.py` fixes black border rectangles caused by a missing `n` operator
  after the clipping path `W` in appearance streams (`fix_ap_streams`) — this runs
  automatically every time a PDF is generated since pypdf regenerates AP streams on each fill.