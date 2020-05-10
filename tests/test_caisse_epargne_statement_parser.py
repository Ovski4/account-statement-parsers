import sys
import json
import os
import pytest

sys.path.append('./modules')
from caisse_epargne_statement_parser import CaisseEpargneStatementParser
from pdf_parser import PdfParser

sys.path.append('./tests/files')
from releve_caisse_epargne import caisse_epargne_lines

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

def testIsHeaderTableLine():

    headerTableLines = [
        [
            {'value': 'Date', 'x0': 142.5, 'x1': 157.28, 'y0': 477.24, 'y1': 469.15},
            {'value': 'Détail des opérations en euros', 'x0': 171.0, 'x1': 265.96, 'y0': 477.24, 'y1': 469.15},
            {'value': 'Débit', 'x0': 462.9, 'x1': 479.24, 'y0': 477.24, 'y1': 469.15},
            {'value': 'Crédit', 'x0': 543.0, 'x1': 561.67, 'y0': 477.24, 'y1': 469.15}
        ],
        [
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
        ],
        [
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
        ]
    ]

    parser = CaisseEpargneStatementParser(headerTableLines)
    assert parser.isHeaderTableLine(headerTableLines[0]) == True
    assert parser.isHeaderTableLine(headerTableLines[1]) == False
    assert parser.isHeaderTableLine(headerTableLines[2]) == False

def testExtractAccountNameRaiseError():

    lines = [
       {'value': 'first line', 'x0': 142.5, 'y0': 756.46, 'x1': 312.5, 'y1': 746.34},
       {'value': 'second line', 'x0': 142.5, 'y0': 748.66, 'x1': 402.81, 'y1': 738.54},
       {'value': 'third line', 'x0': 142.5, 'y0': 748.66, 'x1': 402.81, 'y1': 738.54}
    ]

    parser = CaisseEpargneStatementParser(lines)
    with pytest.raises(Exception):
        parser.extractAccountName(lines[0])

def testIsDateLine():

    lines = [
        [
            {'value': 'au 01/03/2020 - N° 36'}
        ],
        [
            {'value': 'au 01/03/2020 - N° 36 wrong'}
        ]
    ]

    parser = CaisseEpargneStatementParser(lines)
    assert parser.isDateLine(lines[0]) == True
    assert parser.isDateLine(lines[1]) == False

def testLineIsCredit():

    headerTableLine = [
        {'value': 'Date', 'x0': 142.5,'x1': 157.28, 'y0': 477.24, 'y1': 469.15},
        {'value': 'Détail des opérations en euros', 'x0': 171.0, 'x1': 265.96, 'y0': 477.24, 'y1': 469.15},
        {'value': 'Débit', 'x0': 462.9, 'x1': 479.24, 'y0': 477.24, 'y1': 469.15},
        {'value': 'Crédit', 'x0': 543.0, 'x1': 561.67, 'y0': 477.24, 'y1': 469.15}
    ]

    line1 = [
        {'value': '06/02', 'x0': 141.6, 'x1': 159.13, 'y0': 409.14, 'y1': 401.05},
        {'value': 'VIR SEPA BRICODEPOT', 'x0': 170.1, 'x1': 251.13, 'y0': 409.14, 'y1': 401.05},
        {'value': 'Vir BRICODEPOT SE', 'x0': 170.1, 'x1': 235.05, 'y0': 400.74, 'y1': 392.65},
        {'value': '76,00', 'x0': 545.4, 'x1': 562.91, 'y0': 409.14, 'y1': 401.05}
    ]

    line2 = [
        {'value': '17/02', 'x0': 141.6, 'x1': 159.13, 'y0': 350.34, 'y1': 342.25},
        {'value': 'VIR SEPA BRICODEPOT', 'x0': 170.1, 'x1': 251.13, 'y0': 350.34, 'y1': 342.25},
        {'value': 'Vir BRICODEPOT SE', 'x0': 170.1, 'x1': 235.05, 'y0': 341.94, 'y1': 333.85},
        {'value': '7,00', 'x0': 549.6, 'x1': 563.22, 'y0': 350.34, 'y1': 342.25}
    ]

    line3 = [
        {'value': '24/02', 'x0': 141.6, 'x1': 159.13, 'y0': 194.94, 'y1': 186.85},
        {'value': 'VIR SEPA MR PEZIN ARNAUD', 'x0': 170.1, 'x1': 272.93, 'y0': 194.94, 'y1': 186.85},
        {'value': "-Réf. donneur d'ordre :", 'x0': 170.1, 'x1': 235.9, 'y0': 187.49, 'y1': 178.24},
        {'value': 'VIREMENT SEPA PAR INTERNET', 'x0': 241.5, 'x1': 351.57, 'y0': 186.54, 'y1': 178.45},
        {'value': '32,00', 'x0': 545.4, 'x1': 562.91, 'y0': 194.94, 'y1': 186.85}
    ]

    parser = CaisseEpargneStatementParser([line1, line2, line3])
    parser.setColumnBoundaries(headerTableLine)
    assert parser.isCreditLine(line1) == True
    assert parser.isCreditLine(line2) == True
    assert parser.isCreditLine(line3) == True

def testLineIsDebit():

    headerTableLine = [
        {'value': 'Date', 'x0': 142.5, 'x1': 157.28, 'y0': 731.94, 'y1': 723.85},
        {'value': 'Détail des opérations en euros', 'x0': 171.0, 'x1': 265.96, 'y0': 731.94, 'y1': 723.85},
        {'value': 'Débit', 'x0': 462.9, 'x1': 479.24, 'y0': 731.94, 'y1': 723.85},
        {'value': 'Crédit', 'x0': 543.0, 'x1': 561.67, 'y0': 731.94, 'y1': 723.85}
    ]

    line1 = [
        {'value': '07/02', 'x0': 142.5, 'x1': 160.03, 'y0': 592.44, 'y1': 584.35},
        {'value': 'CB PEAGE AUTOROUTE FACT 030220', 'x0': 171.0, 'x1': 298.2, 'y0': 592.44, 'y1': 584.35},
        {'value': '3,80', 'x0': 468.3, 'x1': 481.92, 'y0': 592.14, 'y1': 584.05}
    ]

    line2 = [
        {'value': '03/09', 'x0': 142.5, 'x1': 160.03, 'y0': 129.84, 'y1': 121.75},
        {'value': 'CB REGISTRAIRE FACT 290819 (', 'x0': 171.0, 'x1': 287.5, 'y0': 129.84, 'y1': 121.75},
        {'value': 'E', 'x0': 287.5, 'x1': 291.1, 'y0': 123.2, 'y1': 123.2},
        {'value': 'N', 'x0': 291.1, 'x1': 296.5, 'y0': 123.2, 'y1': 123.2},
        {'value': 'C', 'x0': 298.15, 'x1': 302.95, 'y0': 123.2, 'y1': 123.2},
        {'value': 'A', 'x0': 302.95, 'x1': 307.45, 'y0': 123.2, 'y1': 123.2},
        {'value': 'D', 'x0': 307.45, 'x1': 312.55, 'y0': 123.2, 'y1': 123.2},
        {'value': '9', 'x0': 314.2, 'x1': 317.8, 'y0': 123.2, 'y1': 123.2},
        {'value': ',', 'x0': 317.8, 'x1': 319.3, 'y0': 123.2, 'y1': 123.2},
        {'value': '0', 'x0': 319.3, 'x1': 322.9, 'y0': 123.2, 'y1': 123.2},
        {'value': '0', 'x0': 322.9, 'x1': 326.5, 'y0': 123.2, 'y1': 123.2},
        {'value': ')', 'x0': 326.5, 'x1': 328.6, 'y0': 123.2, 'y1': 123.2},
        {'value': '6,13', 'x0': 468.3, 'x1': 481.92, 'y0': 129.84, 'y1': 121.75}
    ]

    parser = CaisseEpargneStatementParser([line1])
    parser.setColumnBoundaries(headerTableLine)
    assert parser.isDebitLine(line1) == True
    assert parser.isDebitLine(line2) == True

def testGetStatementYear():

    lines = [
        [
            {'value': 'au 01/03/2020 - N° 36'}
        ],
        [
            {'value': 'au 02/05/1999 - N° 37'}
        ],
        [
            {'value': 'au 01/01/1999 - N° 38'}
        ]
    ]

    parser = CaisseEpargneStatementParser(lines)
    assert parser.getStatementYear(lines[0]) == '2020'
    assert parser.getStatementYear(lines[1]) == '1999'
    assert parser.getStatementYear(lines[2]) == '1998'

def testParse():

    parser = CaisseEpargneStatementParser(caisse_epargne_lines)
    transactions = parser.parse()
    with open('./tests/files/expected-results-caisse-epargne.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData
