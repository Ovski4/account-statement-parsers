import sys
sys.path.append('./modules')
from pdf_parser import PdfParser
import unittest

# import ptvsd
# ptvsd.enable_attach(address = ('0.0.0.0', 3000))
# ptvsd.wait_for_attach()

def testFirstLine():
    pdfFile = open('./tests/files/test.pdf', 'rb')
    pdfParser = PdfParser()
    lines = pdfParser.parse(pdfFile)
    pdfFile.close()

    assert len(lines[0]) == 1
    assert lines[0][0]['value'] == 'Text here'
