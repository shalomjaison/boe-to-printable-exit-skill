import sys
import json
import os

from pypdf import PdfReader, PdfWriter


def build_field_map(data):
    """
    Returns a dict of { field_name: value }
    """
    bill_no_value = f"{data['dec_no_part1']}\n{data['dec_no_part2']}"
 
    field_map = {
        'ExporterFormField':           data['exporter'],
        'BillNoFormField':             bill_no_value,
        'DateFormField':               data['dec_date'],
        'COOFormField':                data['country_of_origin'],
        'PointOfExitFormField':        data['point_of_exit'],
        'DestinationFormField':        data['destination'],
        'QuantityFormField':           data['quantity'],
        'DescriptionOfGoodsFormField': data['description'],
        'TotalQuantityFormField':      data['quantity'],
        'TotalWeightFormField':        data['total_weight'],
        'ManifestNoFormField':         data.get('manifest_no', ''),
        'CustomsSealNoFormField':      data.get('customs_seal_no', ''),
        'ContainerNoFormField':        data.get('container_no', ''),
    }
    return field_map


def fill_exit_papers(data, template_path, output_path):
    """
    Main entry point. Fills the template, saves output.
    """
    field_map = build_field_map(data)

    reader = PdfReader(template_path)
    writer = PdfWriter(clone_from=reader)

    writer.update_page_form_field_values(
        writer.pages[0],
        field_map,
        auto_regenerate=False
    )

    writer.set_need_appearances_writer(True)

    with open(output_path, 'wb') as f:
        writer.write(f)

    print(f"✓ Output saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fill_exit_papers.py '<json>' output.pdf")
        sys.exit(1)
 
    data = json.loads(sys.argv[1])
    output_path = sys.argv[2]
    template_path = os.path.join(os.path.dirname(__file__), '../assets/exit_papers_template_patched.pdf')

 
    if not os.path.exists(template_path):
        print(f"Error: template not found: {template_path}")
        sys.exit(1)
 
 
    required_keys = [
        'exporter', 'dec_no_part1', 'dec_no_part2', 'dec_date', 'country_of_origin',
        'point_of_exit', 'destination', 'quantity', 'description', 'total_weight'
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"Error: missing fields: {missing}")
        sys.exit(1)
 
    fill_exit_papers(data, template_path, output_path)

