import sys
import json
import os

sys.path.append('./modules')
from credit_mutuel_statement_parser import CreditMutuelStatementParser
from pdf_parser import PdfParser

sys.path.append('./tests/files')
from releve_credit_mutuel import credit_mutuel_lines_1, credit_mutuel_lines_2

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

def testParse():

    ccmparser = CreditMutuelStatementParser(credit_mutuel_lines_1)
    transactions = ccmparser.parse()
    with open('./tests/files/expected-results-credit-mutuel-1.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

    ccmparser = CreditMutuelStatementParser(credit_mutuel_lines_2)
    transactions = ccmparser.parse()
    with open('./tests/files/expected-results-credit-mutuel-2.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

def testExtractAccountName():

    accountLines = [
        [{'value': 'C/C EUROCOMPTE JEUNE N° 22020325207 en euros', 'x0': 81.6, 'y0': 514.55, 'x1': 331.79, 'y1': 502.65}],
        [{'value': 'LIVRET BLEU N° 11111324203 en euros', 'x0': 81.6, 'y0': 694.55, 'x1': 269.56, 'y1': 682.65}]
    ]

    ccmParser = CreditMutuelStatementParser(accountLines)
    assert ccmParser.extractAccountName(accountLines[0]) == 'C/C EUROCOMPTE JEUNE N° 22020325207'
    assert ccmParser.extractAccountName(accountLines[1]) == 'LIVRET BLEU N° 11111324203'

def testIsAccountNameLine():

    accountLines = [
        [
            {'value': 'C/C EUROCOMPTE JEUNE N° 22020325207 en dollars', 'x0': 81.6, 'x1': 331.79, 'y0': 514.55, 'y1': 502.65}
        ],
        [
            {'value': 'C/C EUROCOMPTE JEUNE N° 22020325207 en euros', 'x0': 81.6, 'x1': 331.79, 'y0': 514.55, 'y1': 502.65}
        ],
        [
            {'value': 'TITULAIRE(S) : M BOB LENON', 'x0': 81.6, 'x1': 291.04, 'y0': 502.55, 'y1': 490.65},
            {'value': 'IBAN : FR76 1027 8072 2800 0203 2420 139', 'x0': 370.8, 'x1': 532.67, 'y0': 500.58, 'y1': 491.06}
        ],
        [
            {'value': 'C/C EUROCOMPTE JEUNE N° 22020325207 en euros', 'x0': 81.6, 'x1': 331.79, 'y0': 514.55, 'y1': 502.65}
        ],
        [
            {'value': 'WRONG', 'x0': 81.6, 'x1': 291.04, 'y0': 502.55, 'y1': 490.65},
            {'value': 'IBAN : FR76 1027 8072 2800 0203 2420 139', 'x0': 370.8, 'x1': 532.67, 'y0': 500.58, 'y1': 491.06}
        ]
    ]

    ccmParser = CreditMutuelStatementParser(accountLines)
    assert ccmParser.isAccountNameLine(0, accountLines) == False
    assert ccmParser.isAccountNameLine(1, accountLines) == True
    assert ccmParser.isAccountNameLine(2, accountLines) == False
    assert ccmParser.isAccountNameLine(3, accountLines) == False
    assert ccmParser.isAccountNameLine(4, accountLines) == False

def testIsHeaderTableLine():

    headerTableLines = [
        [
            {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Date valeur', 'x0': 98.4, 'x1': 141.53, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Opération', 'x0': 160.8, 'x1': 198.58, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Débit euros', 'x0': 415.68, 'x1': 459.69, 'y0': 484.98, 'y1': 475.46},
            {'value': 'Crédit euros', 'x0': 486.96, 'x1': 534.08, 'y0': 484.98, 'y1': 475.46}
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

    ccmParser = CreditMutuelStatementParser(headerTableLines)
    assert ccmParser.isHeaderTableLine(headerTableLines[0]) == True
    assert ccmParser.isHeaderTableLine(headerTableLines[1]) == False
    assert ccmParser.isHeaderTableLine(headerTableLines[2]) == False

def testGetColumnBoundaries():

    headerTableLine = [
        {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Date valeur', 'x0': 98.4, 'x1': 141.53, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Opération', 'x0': 160.8, 'x1': 198.58, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Débit euros', 'x0': 415.68, 'x1': 459.69, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Crédit euros', 'x0': 486.96, 'x1': 534.08, 'y0': 484.98, 'y1': 475.46}
    ]

    expectedData = {
        'date': {
            'x0': 63.36,
            'x1': 80.7
        },
        'date_valeur': {
            'x0': 98.4,
            'x1': 141.53
        },
        'operation': {
            'x0': 147.6,
            'x1': 198.58
        },
        'debit': {
            'x0': 415.68,
            'x1': 459.69
        },
        'credit': {
            'x0': 486.96,
            'x1': 534.08
        },
    }

    ccmParser = CreditMutuelStatementParser(headerTableLine)
    assert ccmParser.getColumnBoundaries(headerTableLine) == expectedData

def testLinesAreWithinBoundaries():

    columnBoundaries = {
        'credit': {'x0': 486.96, 'x1': 534.08},
        'date': {'x0': 63.36, 'x1': 80.7},
        'date_valeur': {'x0': 98.4, 'x1': 141.53},
        'debit': {'x0': 415.68, 'x1': 459.69},
        'operation': {'x0': 160.8, 'x1': 198.58}
    }

    line = [
        {'value': '0', 'x0': 5.9, 'x1': 14.16, 'y0': 279.68, 'y1': 274.58},
        {'value': '08/06/2014', 'x0': 52.08, 'x1': 92.11, 'y0': 279.51, 'y1': 270.26},
        {'value': '08/06/2014', 'x0': 100.08, 'x1': 140.11, 'y0': 279.51, 'y1': 270.26},
        {'value': 'VIR SEPA COURSES + ...MUR DE LY', 'x0': 147.6, 'x1': 290.98, 'y0': 279.51, 'y1': 270.26},
        {'value': '28,40', 'x0': 439.68, 'x1': 459.7, 'y0': 279.51, 'y1': 270.26}
    ]

    ccmParser = CreditMutuelStatementParser([])
    assert ccmParser.linesAreWithinBoundaries(line[1], columnBoundaries['date']) == True

def testLineIsDebit():

    headerTableLine = [
        {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46 },
        {'value': 'Date valeur', 'x0': 98.4, 'x1': 141.53, 'y0': 484.98, 'y1': 475.46 },
        {'value': 'Opération', 'x0': 160.8, 'x1': 198.58, 'y0': 484.98, 'y1': 475.46 },
        {'value': 'Débit EUROS', 'x0': 408.96, 'x1': 459.63, 'y0': 484.98, 'y1': 475.46 },
        {'value': 'Crédit EUROS', 'x0': 480.24, 'x1': 534.02, 'y0': 484.98, 'y1': 475.46 }
    ]

    line = [
        {'value': '08/11/2019', 'x0': 52.08, 'x1': 92.11, 'y0': 152.79, 'y1': 143.54 },
        {'value': '08/11/2019', 'x0': 100.08, 'x1': 140.11, 'y0': 152.79, 'y1': 143.54 },
        {'value': 'PAIEMENT CB 0711 RUNGIS', 'x0': 147.6, 'x1': 257.41, 'y0': 152.79, 'y1': 143.54 },
        {'value': '10,37', 'x0': 439.68, 'x1': 459.7, 'y0': 152.79, 'y1': 143.54 }
    ]

    ccmParser = CreditMutuelStatementParser([line])
    ccmParser.setColumnBoundaries(headerTableLine)
    assert ccmParser.isDebitLine(line) == True

def testOtherLineIsDebit():

    headerTableLine = [
        {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Date valeur', 'x0': 98.4, 'x1': 141.53, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Opération', 'x0': 160.8, 'x1': 198.58, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Débit euros', 'x0': 415.68, 'x1': 459.69, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Crédit euros', 'x0': 486.96, 'x1': 534.08, 'y0': 484.98, 'y1': 475.46}
    ]

    lines = [
        [
            {'value': '02/05/2014', 'x0': 52.08, 'x1': 92.11, 'y0': 448.47, 'y1': 439.22},
            {'value': '02/05/2014', 'x0': 100.08, 'x1': 140.11, 'y0': 448.47, 'y1': 439.22},
            {'value': 'PAIEMENT CB 0105 RUST', 'x0': 147.6, 'x1': 248.07, 'y0': 448.47, 'y1': 439.22},
            {'value': '29,50', 'x0': 439.68, 'x1': 459.7, 'y0': 448.47, 'y1': 439.22}
        ],
        [
            {'value': 'EUROPA PARK GMBH CA... 02892630', 'x0': 147.6, 'x1': 298.76, 'y0': 437.91, 'y1': 428.66}
        ],
        [
            {'value': '03/05/2014', 'x0': 52.08, 'x1': 92.11, 'y0': 321.75, 'y1': 312.5},
            {'value': '03/05/2014', 'x0': 100.08, 'x1': 140.11, 'y0': 321.75, 'y1': 312.5},
            {'value': 'VIRT PARENTS', 'x0': 147.6, 'x1': 205.83, 'y0': 321.75, 'y1': 312.5},
            {'value': '350,00', 'x0': 509.52, 'x1': 533.98, 'y0': 321.75, 'y1': 312.5}
        ]
    ]

    ccmParser = CreditMutuelStatementParser(lines)
    ccmParser.setColumnBoundaries(headerTableLine)
    assert ccmParser.isDebitLine(lines[0]) == True
    assert ccmParser.isDebitLine(lines[1]) == False
    assert ccmParser.isDebitLine(lines[2]) == False

def testExtractTransaction():

    headerTableLine = [
        {'value': 'Date', 'x0': 63.36, 'x1': 80.7, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Date valeur', 'x0': 98.4, 'x1': 141.53, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Opération', 'x0': 160.8, 'x1': 198.58, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Débit euros', 'x0': 415.68, 'x1': 459.69, 'y0': 484.98, 'y1': 475.46},
        {'value': 'Crédit euros', 'x0': 486.96, 'x1': 534.08, 'y0': 484.98, 'y1': 475.46}
    ]

    lines = [
        [
            {'value': '02/05/2014', 'x0': 52.08, 'x1': 92.11, 'y0': 448.47, 'y1': 439.22},
            {'value': '02/05/2014', 'x0': 100.08, 'x1': 140.11, 'y0': 448.47, 'y1': 439.22},
            {'value': 'PAIEMENT CB 0105 RUST', 'x0': 147.6, 'x1': 248.07, 'y0': 448.47, 'y1': 439.22},
            {'value': '29,50', 'x0': 439.68, 'x1': 459.7, 'y0': 448.47, 'y1': 439.22}
        ],
        [
            {'value': 'EUROPA PARK GMBH CARTE 02892630', 'x0': 147.6, 'x1': 298.76, 'y0': 437.91, 'y1': 428.66}
        ],
        [
            {'value': '03/05/2014', 'x0': 52.08, 'x1': 92.11, 'y0': 321.75, 'y1': 312.5},
            {'value': '03/05/2014', 'x0': 100.08, 'x1': 140.11, 'y0': 321.75, 'y1': 312.5},
            {'value': 'VIRT PARENTS', 'x0': 147.6, 'x1': 205.83, 'y0': 321.75, 'y1': 312.5},
            {'value': '350,00', 'x0': 509.52, 'x1': 533.98, 'y0': 321.75, 'y1': 312.5}
        ]
    ]

    ccmParser = CreditMutuelStatementParser(lines)
    ccmParser.setColumnBoundaries(headerTableLine)
    ccmParser.currentAccount = 'acc 09879'

    assert ccmParser.extractTransaction(0, lines, 'debit') == {
        'account': 'acc 09879',
        'date': '02/05/2014',
        'label': 'PAIEMENT CB 0105 RUST EUROPA PARK GMBH CARTE 02892630',
        'value': -29.50
    }
