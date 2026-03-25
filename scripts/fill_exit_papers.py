import sys
import json
import os

from pypdf import PdfReader, PdfWriter

FONT_SIZES = {
    'ExporterFormField':           9,
    'BillNoFormField':             7,
    'DateFormField':               9,
    'COOFormField':                9,
    'PointOfExitFormField':        9,
    'DestinationFormField':        9,
    'QuantityFormField':           8,
    'DescriptionOfGoodsFormField': 7,
    'TotalQuantityFormField':      8,
    'TotalWeightFormField':        8,
}

MULTILINE_FIELDS = {'BillNoFormField', 'DescriptionOfGoodsFormField'}

def base_name(field_name):
    if (field_name.endswith('2') or field_name.endswith('3')) and field_name[:-1] in FONT_SIZES:
        return field_name[:-1]
    return field_name

def build_field_map(data):
    """
    Returns a dict of { page_number: { field_name: value } }
    covering all 3 pages of the certificate.
    """
    bill_no_value = f"{data['dec_no_part1']}\n{data['dec_no_part2']}"
 
    pages = {}
    for suffix, page_num in [('', 1), ('2', 2), ('3', 3)]:
        pages[page_num] = {
            f'ExporterFormField{suffix}':           data['exporter'],
            f'BillNoFormField{suffix}':             bill_no_value,
            f'DateFormField{suffix}':               data['dec_date'],
            f'COOFormField{suffix}':                data['country_of_origin'],
            f'PointOfExitFormField{suffix}':        data['point_of_exit'],
            f'DestinationFormField{suffix}':        data['destination'],
            f'QuantityFormField{suffix}':           data['quantity'],
            f'DescriptionOfGoodsFormField{suffix}': data['description'],
            f'TotalQuantityFormField{suffix}':      data['quantity'],
            f'TotalWeightFormField{suffix}':        data['total_weight'],
        }
    return pages


def fill_exit_papers(data, template_path, output_path):
    """
    Main entry point. Patches the template, fills all 3 pages, saves output.
    """
    field_map = build_field_map(data)

    reader = PdfReader(template_path)
    writer = PdfWriter(clone_from=reader)

    for page_num, field_values in field_map.items():
        writer.update_page_form_field_values(
            writer.pages[page_num - 1],
            field_values,
            auto_regenerate=False
        )

    writer.set_need_appearances_writer(True)

    with open(output_path, 'wb') as f:
        writer.write(f)

    print(f"✓ Output saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fill_exit_papers.py data.json template.pdf output.pdf")
        sys.exit(1)
 
    data_path, template_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
 
    if not os.path.exists(data_path):
        print(f"Error: data file not found: {data_path}")
        sys.exit(1)
    if not os.path.exists(template_path):
        print(f"Error: template not found: {template_path}")
        sys.exit(1)
 
    with open(data_path, 'r') as f:
        data = json.load(f)
 
    required_keys = [
        'exporter', 'dec_no_part1', 'dec_no_part2', 'dec_date', 'country_of_origin',
        'point_of_exit', 'destination', 'quantity', 'description', 'total_weight'
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"Error: missing fields in data.json: {missing}")
        sys.exit(1)
 
    fill_exit_papers(data, template_path, output_path)

