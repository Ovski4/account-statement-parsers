import sys
sys.path.append('./modules')
from caisse_epargne_statement_parser import CaisseEpargneStatementParser
from pdf_parser import PdfParser
import json
import unittest

# import ptvsd
# ptvsd.enable_attach(address = ('0.0.0.0', 3000))
# ptvsd.wait_for_attach()

class TestCaisseEpargneStatementParser(unittest.TestCase):

    def testIsHeaderTableLine(self):
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

        print("\nAssert the line is a header of a table line")
        parser = CaisseEpargneStatementParser(headerTableLines)
        self.assertEqual(parser.isHeaderTableLine(headerTableLines[0]), True)
        self.assertEqual(parser.isHeaderTableLine(headerTableLines[1]), False)
        self.assertEqual(parser.isHeaderTableLine(headerTableLines[2]), False)

    def testIsDateLine(self):
        lines = [
            [
                {'value': 'au 01/03/2020 - N° 36'}
            ],
            [
                {'value': 'au 01/03/2020 - N° 36 wrong'}
            ]
        ]

        print("\nAssert the line is a date line")
        parser = CaisseEpargneStatementParser(lines)
        self.assertEqual(parser.isDateLine(lines[0]), True)
        self.assertEqual(parser.isDateLine(lines[1]), False)

    def testLineIsCredit(self):
        print("\nAssert the line is a credit line")

        headerTableLine = [
            {'value': 'Date', 'x0': 142.5,'x1': 157.28, 'y0': 477.24, 'y1': 469.15},
            {'value': 'Détail des opérations en euros', 'x0': 171.0, 'x1': 265.96, 'y0': 477.24, 'y1': 469.15},
            {'value': 'Débit', 'x0': 462.9, 'x1': 479.24, 'y0': 477.24, 'y1': 469.15},
            {'value': 'Crédit', 'x0': 543.0, 'x1': 561.67, 'y0': 477.24, 'y1': 469.15}
        ]

        line1 = [
            {'value': '06/02', 'x0': 141.6, 'x1': 159.13, 'y0': 409.14, 'y1': 401.05},
            {'value': 'VIR SEPA DECATHLON', 'x0': 170.1, 'x1': 251.13, 'y0': 409.14, 'y1': 401.05},
            {'value': 'Vir DECATHLON SE', 'x0': 170.1, 'x1': 235.05, 'y0': 400.74, 'y1': 392.65},
            {'value': '76,00', 'x0': 545.4, 'x1': 562.91, 'y0': 409.14, 'y1': 401.05}
        ]

        line2 = [
            {'value': '17/02', 'x0': 141.6, 'x1': 159.13, 'y0': 350.34, 'y1': 342.25},
            {'value': 'VIR SEPA DECATHLON', 'x0': 170.1, 'x1': 251.13, 'y0': 350.34, 'y1': 342.25},
            {'value': 'Vir DECATHLON SE', 'x0': 170.1, 'x1': 235.05, 'y0': 341.94, 'y1': 333.85},
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
        self.assertEqual(parser.isCreditLine(line1), True)
        self.assertEqual(parser.isCreditLine(line2), True)
        self.assertEqual(parser.isCreditLine(line3), True)

    def testLineIsDebit(self):
        print("\nAssert the line is a debit line")

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

        parser = CaisseEpargneStatementParser([line1])
        parser.setColumnBoundaries(headerTableLine)
        self.assertEqual(parser.isDebitLine(line1), True)

    def testGetStatementYear(self):
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

        print("\nAssert the statement year is correctly retrieved")
        parser = CaisseEpargneStatementParser(lines)
        self.assertEqual(parser.getStatementYear(lines[0]), '2020')
        self.assertEqual(parser.getStatementYear(lines[1]), '1999')
        self.assertEqual(parser.getStatementYear(lines[2]), '1998')

    def testParse(self):
        print("\nAssert the files are correctly parsed")

        pdfFile = open('./tests/files/releve-caisse-epargne.pdf', 'rb')
        self.lines = PdfParser().parse(pdfFile)
        pdfFile.close()
        parser = CaisseEpargneStatementParser(self.lines)
        transactions = parser.parse()
        with open('./tests/files/expected-results-caisse-epargne.json') as file:
            expectedData = json.loads(file.read())
        self.assertEqual(transactions, expectedData)

if __name__ == '__main__':
    unittest.main()
