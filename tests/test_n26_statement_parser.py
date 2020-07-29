import sys
import json
import os
import pytest

sys.path.append('./modules')
from n26_statement_parser import N26StatementParser
from pdf_parser import PdfParser

sys.path.append('./tests/files')
from releve_n26 import n26_lines

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

def testParse():

    n26parser = N26StatementParser(n26_lines)
    transactions = n26parser.parse()
    with open('./tests/files/expected-results-n26.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData
