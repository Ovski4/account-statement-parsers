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

    parser = N26StatementParser(n26_lines)
    transactions = parser.parse()
    with open('./tests/files/expected-results-n26.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

def testIsDateLine():

    parser = N26StatementParser(n26_lines)

    line1 = [{ 'value': 'vendredi, 17. juillet 2020' }]
    assert parser.isDateLine(line1) == True

    line2 = [{ 'value': 'mercredi, 29. juillet 2020' }]
    assert parser.isDateLine(line2) == True

    line3 = [{ 'value': '15. juillet 2020 - 29. juillet 2020' }]
    assert parser.isDateLine(line3) == False

def testExtractDateFromLine():
    parser = N26StatementParser(n26_lines)

    line1 = [{ 'value': 'vendredi, 17. juillet 2020' }]
    assert parser.extractDateFromLine(line1) == '17/07/2020'

    line2 = [{ 'value': 'mercredi, 29. juillet 2020' }]
    assert parser.extractDateFromLine(line2) == '29/07/2020'

def testLineIsTransactionLabel():
    parser = N26StatementParser(n26_lines)

    line1 = [{
        'value': 'M HECTOR MALONDA',
        'x0': 30.0,
        'y0': 597.05,
        'x1': 162.29,
        'y1': 583.91
    }]
    assert parser.lineIsTransactionLabel(line1) == True

    line2 = [{
        'value': 'NANTES MANGIN',
        'x0': 30.0,
        'y0': 485.98,
        'x1': 114.79,
        'y1': 472.84
    }, {
        'value': '-30,00€',
        'x0': 523.28,
        'y0': 478.25,
        'x1': 565.26,
        'y1': 463.47
    }]
    assert parser.lineIsTransactionLabel(line2) == True

    line3 = [{
        'value': 'Mastercard • Distributeur automatique',
        'x0': 30.0,
        'y0': 466.99,
        'x1': 182.66,
        'y1': 455.69
    }]
    assert parser.lineIsTransactionLabel(line3) == False

    line4 = [{
        'value': 'IBAN: FR7610278072280002032420139 • BIC: CMCIFR2AXXX',
        'x0': 30.0,
        'y0': 399.49,
        'x1': 274.14,
        'y1': 388.19
    }]
    assert parser.lineIsTransactionLabel(line4) == False

def testLineHasTransationValue():
    parser = N26StatementParser(n26_lines)

    line1 = [{
        'value': 'NANTES MANGIN',
        'x0': 30.0,
        'y0': 485.98,
        'x1': 114.79,
        'y1': 472.84
    }, {
        'value': '-30,00€',
        'x0': 523.28,
        'y0': 478.25,
        'x1': 565.26,
        'y1': 463.47
    }]

    assert parser.lineHasTransactionValue(line1) == True

def testExtractTransationValue():
    parser = N26StatementParser(n26_lines)

    line1 = [{
        'value': 'NANTES MANGIN',
        'x0': 30.0,
        'y0': 485.98,
        'x1': 114.79,
        'y1': 472.84
    }, {
        'value': '-30,05€',
        'x0': 523.28,
        'y0': 478.25,
        'x1': 565.26,
        'y1': 463.47
    }]

    assert parser.extractTransactionValue(line1) == -30.05
