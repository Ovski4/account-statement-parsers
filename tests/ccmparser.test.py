import sys
sys.path.append('./modules')
from ccmparser import CCMParser
import unittest

# import ptvsd
# ptvsd.enable_attach(address = ('0.0.0.0', 3000))
# ptvsd.wait_for_attach()

class TestCCMParser(unittest.TestCase):

    def setUp(self):
        self.lines = [
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

    def testLineContains(self):
        print("\nAssert the line is an account name line")
        ccmParser = CCMParser(self.lines)
        self.assertEqual(ccmParser.isAccountNameLine(0), False)
        self.assertEqual(ccmParser.isAccountNameLine(1), True)
        self.assertEqual(ccmParser.isAccountNameLine(2), False)
        self.assertEqual(ccmParser.isAccountNameLine(3), False)
        self.assertEqual(ccmParser.isAccountNameLine(4), False)

if __name__ == '__main__':
    unittest.main()