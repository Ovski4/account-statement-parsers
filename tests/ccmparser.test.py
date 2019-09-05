import sys
sys.path.append('./modules')
from ccmparser import CCMParser
import unittest

# import ptvsd
# ptvsd.enable_attach(address = ('0.0.0.0', 3000))
# ptvsd.wait_for_attach()

class TestCCMParser(unittest.TestCase):

    def testLineContains(self):
        print("\nAssert the line is an account name line")

        accountLines = [
            [
                {'value': 'C/C EUROCOMPTE JEUNE N° 00020324201 en dollars', 'x0': 81.6, 'x1': 331.79, 'y0': 514.55, 'y1': 502.65}
            ],
            [
                {'value': 'C/C EUROCOMPTE JEUNE N° 00020324201 en euros', 'x0': 81.6, 'x1': 331.79, 'y0': 514.55, 'y1': 502.65}
            ],
            [
                {'value': 'TITULAIRE(S) : M BAPTISTE BOUCHEREAU', 'x0': 81.6, 'x1': 291.04, 'y0': 502.55, 'y1': 490.65},
                {'value': 'IBAN : FR76 1027 8072 2800 0203 2420 139', 'x0': 370.8, 'x1': 532.67, 'y0': 500.58, 'y1': 491.06}
            ],
            [
                {'value': 'C/C EUROCOMPTE JEUNE N° 00020324201 en euros', 'x0': 81.6, 'x1': 331.79, 'y0': 514.55, 'y1': 502.65}
            ],
            [
                {'value': 'WRONG', 'x0': 81.6, 'x1': 291.04, 'y0': 502.55, 'y1': 490.65},
                {'value': 'IBAN : FR76 1027 8072 2800 0203 2420 139', 'x0': 370.8, 'x1': 532.67, 'y0': 500.58, 'y1': 491.06}
            ]
        ]

        ccmParser = CCMParser(accountLines)
        self.assertEqual(ccmParser.isAccountNameLine(0), False)
        self.assertEqual(ccmParser.isAccountNameLine(1), True)
        self.assertEqual(ccmParser.isAccountNameLine(2), False)
        self.assertEqual(ccmParser.isAccountNameLine(3), False)
        self.assertEqual(ccmParser.isAccountNameLine(4), False)

    def testIsHeaderTableLine(self):
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

        print("\nAssert the line is a header of a table line")
        ccmParser = CCMParser(headerTableLines)
        self.assertEqual(ccmParser.isHeaderTableLine(headerTableLines[0]), True)
        self.assertEqual(ccmParser.isHeaderTableLine(headerTableLines[1]), False)
        self.assertEqual(ccmParser.isHeaderTableLine(headerTableLines[2]), False)

    def testGetColumnBoundaries(self):
        print("\Assert we get the right table column x boundaries from the data")

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
                'x0': 160.8,
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
        ccmParser = CCMParser(headerTableLine)
        self.assertEqual(ccmParser.getColumnBoundaries(headerTableLine), expectedData)

    def testLineIsDebit(self):
        print("\nAssert the line is a debit line")

        debitLines = [
            [
                {'value': '02/05/2014', 'x0': 52.08, 'x1': 92.11, 'y0': 448.47, 'y1': 439.22},
                {'value': '02/05/2014', 'x0': 100.08, 'x1': 140.11, 'y0': 448.47, 'y1': 439.22},
                {'value': 'PAIEMENT CB 0105 RUST', 'x0': 147.6, 'x1': 248.07, 'y0': 448.47, 'y1': 439.22},
                {'value': '29,50', 'x0': 439.68, 'x1': 459.7, 'y0': 448.47, 'y1': 439.22}
            ],
            [
                {'value': 'EUROPA PARK GMBH CA... 02892630', 'x0': 147.6, 'x1': 298.76, 'y0': 437.91, 'y1': 428.66}
            ]
        ]

        ccmParser = CCMParser(debitLines)
        # self.assertEqual(ccmParser.isAccountNameLine(0), False)

if __name__ == '__main__':
    unittest.main()