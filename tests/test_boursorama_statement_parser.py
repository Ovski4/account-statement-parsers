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

# pdfFile = open('/usr/src/app/tests/files/releve-boursorama.pdf', 'rb')
# lines = PdfParser().parse(pdfFile)
# f = open( '/usr/src/app/tests/files/file.py', 'w' )
# f.write( 'lines = ' + repr(lines) + '\n' )
# f.close()
# pdfFile.close()

def testIsLabelWord():

    lines = [
        { 'value': 'VIR VIREMENT CREATION COMPTE', 'x0': 82.8, 'y0': 500.86, 'x1': 217.2, 'y1': 492.45},
        {'value': 'BOURSORAMA', 'x0': 82.8, 'y0': 488.86, 'x1': 145.2, 'y1': 480.45},
        {'value': 'BRS80', 'x0': 82.8, 'y0': 476.86, 'x1': 111.6, 'y1': 468.45},
        {'value': 'Réf : DDDDFRPP847C0120230829105811111', 'x0': 82.8, 'y0': 392.86, 'x1': 274.8, 'y1': 384.45},
        {'value': 'Nouveau solde en EUR :', 'x0': 158.4, 'y0': 208.85, 'x1': 262.42, 'y1': 198.14},
        {'value': '2.553,00', 'x0': 439.2, 'y0': 206.86, 'x1': 535.2, 'y1': 198.45}
    ]

    parser = BoursoramaStatementParser(lines)
    assert parser.isLabelWord(lines[0]) == True
    assert parser.isLabelWord(lines[1]) == True
    assert parser.isLabelWord(lines[2]) == True
    assert parser.isLabelWord(lines[3]) == True
    assert parser.isLabelWord(lines[4]) == True
    assert parser.isLabelWord(lines[5]) == False

def testIsDateWord():

    lines = [
        {'value': '18/08/2020', 'x0': 32.4, 'y0': 500.86, 'x1': 80.4, 'y1': 492.45},
        {'value': '18/08/2020', 'x0': 306.0, 'y0': 500.86, 'x1': 354.0, 'y1': 492.45},
        {'value': '2.553,00', 'x0': 439.2, 'y0': 206.86, 'x1': 535.2, 'y1': 198.45}
    ]

    parser = BoursoramaStatementParser(lines)
    assert parser.isDateWord(lines[0]) == True
    assert parser.isDateWord(lines[1]) == False
    assert parser.isDateWord(lines[2]) == False

def testIsCreditWord():

    lines = [
        {'value': '18/08/2020', 'x0': 32.4, 'y0': 500.86, 'x1': 80.4, 'y1': 492.45},
        {'value': '1.473,00', 'x0': 453.6, 'y0': 464.86, 'x1': 535.2, 'y1': 456.45}
    ]

    parser = BoursoramaStatementParser(lines)
    assert parser.isCreditWord(lines[0]) == False
    assert parser.isCreditWord(lines[1]) == True

def testIsCreditLine():
    line =[
        {
            'value': '31/08/2020',
            'x0': 32.4,
            'y0': 416.86,
            'x1': 80.4,
            'y1': 408.45
        }, {
            'value': 'VIR SEPA MLLE DEBONARD HELENE',
            'x0': 82.8,
            'y0': 416.86,
            'x1': 217.2,
            'y1': 408.45
        }, {
            'value': '31/08/2020',
            'x0': 306.0,
            'y0': 416.86,
            'x1': 354.0,
            'y1': 408.45
        }, {
            'value': '700,00',
            'x0': 453.6,
            'y0': 416.86,
            'x1': 535.2,
            'y1': 408.45
        }
    ]

    parser = BoursoramaStatementParser([line])
    assert parser.isCreditLine(line) == True

def testIsBankAccountLine():
    line = [
        {'value': '2/09/2020', 'x0': 32.4, 'y0': 574.54, 'x1': 74.93, 'y1': 564.14},
        {'value': '40618', 'x0': 82.8, 'y0': 574.54, 'x1': 107.82, 'y1': 564.14},
        {'value': '83333', 'x0': 118.8,'y0': 574.54, 'x1': 143.82,'y1': 564.14},
        {'value': '00340977444','x0': 147.6,'y0': 574.54, 'x1': 202.64,'y1': 564.14},
        {'value': '58','x0': 216.0,'y0': 574.54, 'x1': 226.01,'y1': 564.14},
        {'value': 'EUR','x0': 234.0,'y0': 574.54, 'x1': 253.0,'y1': 564.14},
        {'value': '18/08/2020','x0': 270.0,'y0': 574.54, 'x1': 315.04,'y1': 564.14},
        {'value': '31/08/2020','x0': 334.8,'y0': 574.54, 'x1': 379.84,'y1': 564.14},
        {'value': '300,00 ¤','x0': 388.8,'y0': 574.54, 'x1': 438.84,'y1': 564.14},
        {'value': '0,000000 %','x0': 457.2,'y0': 574.54, 'x1': 510.24,'y1': 564.14},
        {'value': '1','x0': 514.8,'y0': 574.54, 'x1': 527.31,'y1': 564.14 }
    ]

    parser = BoursoramaStatementParser([line])
    assert parser.isBankAccountLine(line) == True

def testIsDate():
    parser = BoursoramaStatementParser([])
    assert parser.isDate('2/09/2020') == True
    assert parser.isDate('31/08/2020') == True
    assert parser.isDate('3a/08/2020') == False
