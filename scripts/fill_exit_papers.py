import sys
import json
import os
import tempfile

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, DictionaryObject, NumberObject, ByteStringObject

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

def patch_template(template_path, patched_path):
    pass