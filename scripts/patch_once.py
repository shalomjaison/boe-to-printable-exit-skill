## Only run this script once to patch the template. The template is already patched in the assets folder, but if you feel the need to patch it again, run this script.
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, NumberObject, ByteStringObject, ArrayObject, FloatObject, DecodedStreamObject

DUBAI_CUSTOMS_FONT_SIZES = {
    'ExporterFormField':           9,
    'BillNoFormField':             7,
    'DecDateFormField':               9,
    'COOFormField':                9,
    'PointOfExitFormField':        9,
    'DestinationFormField':        9,
    'QuantityFormField':           8,
    'DescriptionOfGoodsFormField': 7,
    'TotalQuantityFormField':      8,
    'TotalWeightFormField':        8,
    'ManifestNoFormField':         9,
    'CustomsSealNoFormField':      9,
    'ContainerNoFormField':        9,
    'ExecutionDateFormField':      9,
    'AirwayBillReferenceNoFormField':       9,
}

SHARJAH_CUSTOMS_FONT_SIZES = {
    'ExporterFormField':           8,
    'BillNoFormField':             7,
    'DateFormField':               9,
    'COOFormField':                9,
    'PointOfExitFormField':        9,
    'DestinationFormField':        9,
    'QuantityFormField':           7,
    'DescriptionOfGoodsFormField': 7,
    'TotalQuantityFormField':      8,
    'TotalWeightFormField':        8,
    'ManifestNoFormField':         7,
    'CustomsSealNoFormField':      9,
    'ContainerNoFormField':        9,
    'ExecutionDateFormField':      9,
    'AirwayBillNoFormField':       9,
    'ValueFormField':              8,
}

MULTILINE_FIELDS = {'BillNoFormField', 'DescriptionOfGoodsFormField'}

def remove_field_borders(writer):
    acroform = writer._root_object['/AcroForm'].get_object()
    for field_ref in acroform['/Fields']:
        field = field_ref.get_object()
        field[NameObject('/Border')] = ArrayObject([
            FloatObject(0), FloatObject(0), FloatObject(0)
        ])
        field[NameObject('/BS')] = DictionaryObject({
            NameObject('/W'): NumberObject(0),
            NameObject('/S'): NameObject('/S')
        })
        # Remove white background fill and border color from MK
        mk = field.get('/MK', None)
        if mk:
            mk_obj = mk.get_object() if hasattr(mk, 'get_object') else mk
            if NameObject('/BG') in mk_obj:
                del mk_obj[NameObject('/BG')]
            mk_obj[NameObject('/BC')] = ArrayObject([])

def remove_page_content_streams(writer):
    for page in writer.pages:
        empty_stream = DecodedStreamObject()
        empty_stream.set_data(b'')
        page[NameObject('/Contents')] = writer._add_object(empty_stream)


def patch_template(template_path, patched_path, font_sizes):
    reader = PdfReader(template_path)
    writer = PdfWriter(clone_from=reader)

    helvetica_font = DictionaryObject({
        NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/Type1'),
        NameObject('/BaseFont'): NameObject('/Helvetica'),
        NameObject('/Encoding'): NameObject('/WinAnsiEncoding'),
    })

    font_ref = writer._add_object(helvetica_font)

    acroform = writer._root_object['/AcroForm'].get_object()
    acroform[NameObject('/DR')] = DictionaryObject({
        NameObject('/Font'): DictionaryObject({
            NameObject('/Helv'): font_ref
        })
    })
    acroform[NameObject('/DA')] = ByteStringObject(b'/Helv 9 Tf 0 g')
 
    # Set per-field /DA (font size) and multiline flag where needed
    for field_ref in acroform['/Fields']:
        field = field_ref.get_object()
        name = str(field.get('/T', ''))
 
        if name in font_sizes:
            field[NameObject('/DA')] = ByteStringObject(
                f'/Helv {font_sizes[name]} Tf 0 g'.encode()
            )
            current_flags = int(field.get('/Ff', 0))
            field[NameObject('/Ff')] = NumberObject(current_flags | 4096)
    
    remove_page_content_streams(writer)
    remove_field_borders(writer)
 
    with open(patched_path, 'wb') as f:
        writer.write(f)

if __name__ == "__main__":
    import sys
    authority = sys.argv[1] if len(sys.argv) > 1 else 'dubai'
    if authority == 'sharjah':
        patch_template('../assets/SharjahCustomsExitFormFields.pdf', '../assets/sharjah_exit_template_patched.pdf', SHARJAH_CUSTOMS_FONT_SIZES)
    else:
        patch_template('../assets/DubaiCustomsExitFormFields.pdf', '../assets/dubai_exit_template_patched.pdf', DUBAI_CUSTOMS_FONT_SIZES)

