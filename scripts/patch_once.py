## Only run this script once to patch the template. The template is already patched in the assets folder, but if you feel the need to patch it again, run this script.
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, NumberObject, ByteStringObject, ArrayObject, FloatObject, DecodedStreamObject

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
    'ManifestNoFormField':         9,
    'CustomsSealNoFormField':      9,
    'ContainerNoFormField':        9,
    'ExecutionDateFormField':      9,
    'AirwayBillNoFormField':       9,
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


def patch_template(template_path, patched_path):
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
 
        if name in FONT_SIZES:
            field[NameObject('/DA')] = ByteStringObject(
                f'/Helv {FONT_SIZES[name]} Tf 0 g'.encode()
            )
            if name in MULTILINE_FIELDS:
                current_flags = int(field.get('/Ff', 0))
                field[NameObject('/Ff')] = NumberObject(current_flags | 4096)
    
    remove_page_content_streams(writer)
    remove_field_borders(writer)
 
    with open(patched_path, 'wb') as f:
        writer.write(f)

if __name__ == "__main__":
    patch_template('../assets/BillOfEntry_FormFields.pdf', '../assets/exit_papers_template_patched.pdf')


