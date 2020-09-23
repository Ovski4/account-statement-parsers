import sys
import json
import os
import pytest

sys.path.append('./modules')
from boursorama_statement_parser import BoursoramaStatementParser
from pdf_parser import PdfParser

sys.path.append('./tests/files')
from releve_boursorama import boursorama_lines

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

def testParse():

    parser = BoursoramaStatementParser(boursorama_lines)
    transactions = parser.parse()
    with open('./tests/files/expected-results-boursorama.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData
