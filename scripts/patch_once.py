## Only run this script once to patch the template. The template is already patched in the assets folder, but if you feel the need to patch it again, run this script.


from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, NumberObject, ByteStringObject
from fill_exit_papers import base_name, FONT_SIZES, MULTILINE_FIELDS

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
        base = base_name(name)
 
        if base in FONT_SIZES:
            field[NameObject('/DA')] = ByteStringObject(
                f'/Helv {FONT_SIZES[base]} Tf 0 g'.encode()
            )
            if base in MULTILINE_FIELDS:
                current_flags = int(field.get('/Ff', 0))
                field[NameObject('/Ff')] = NumberObject(current_flags | 4096)
 
    with open(patched_path, 'wb') as f:
        writer.write(f)

if __name__ == "__main__":
    patch_template('../assets/exit_papers_template.pdf', '../assets/exit_papers_template_patched.pdf')


