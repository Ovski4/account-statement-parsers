import sys
import json
import os
import pytest

sys.path.append('./modules')
from n26_statement_parser import N26StatementParser
from pdf_parser import PdfParser

sys.path.append('./tests/files')
from releve_n26_v2_1 import n26_v2_1_lines
from releve_n26_v2_2 import n26_v2_2_lines

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

def testParse():

    n26parser = N26StatementParser(n26_v2_1_lines)
    transactions = n26parser.parse()
    with open('./tests/files/expected-results-n26-v2-1.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

    n26parser = N26StatementParser(n26_v2_2_lines)
    transactions = n26parser.parse()
    with open('./tests/files/expected-results-n26-v2-2.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

def testLinesAreNotWithinBoundaries():

    word1 = {
		'value': '27.09.2020',
		'x0': 389.1,
		'y0': 372.64,
		'x1': 448.03,
		'y1': 357.53
	}

    word2 = {
		'value': '27.09.2020',
		'x0': 389.1,
		'y0': 372.64,
		'x1': 448.03,
		'y1': 357.53
	}

    n26parser = N26StatementParser([])
    assert n26parser.linesAreWithinBoundaries(word1, {'x0': 63.36, 'x1': 80.7}) == False
    assert n26parser.linesAreWithinBoundaries(word2, {'x0': 390.36, 'x1': 400}) == True