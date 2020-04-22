import sys
sys.path.append('./modules')
from line_reader import LineReader
import unittest

# import ptvsd
# ptvsd.enable_attach(address = ('0.0.0.0', 3000))
# ptvsd.wait_for_attach()

class TestLineReader(unittest.TestCase):

    def setUp(self):
        self.line = [
            {'value': 'Caisse', 'x0': 481.2, 'x1': 508.7, 'y0': 550.46, 'y1': 540.06},
            {'value': '07228', 'x0': 512.64, 'x1': 537.66, 'y0': 550.46, 'y1': 540.06},
            {'value': 'RELEVE ET INFORMATIONS BANCAIRES', 'x0': 48.0, 'x1': 285.35, 'y0': 553.72, 'y1': 539.44}
        ]

    def testLineContains(self):
        print("\nAssert the line contains a word")
        lineReader = LineReader(self.line)
        self.assertEqual(lineReader.contains('INFORMA'), True)
        self.assertEqual(lineReader.contains('INFOMA'), False)

if __name__ == '__main__':
    unittest.main()