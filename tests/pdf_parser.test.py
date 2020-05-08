import sys
sys.path.append('./modules')
from pdf_parser import PdfParser
import unittest

# import ptvsd
# ptvsd.enable_attach(address = ('0.0.0.0', 3000))
# ptvsd.wait_for_attach()

class TestPdfParser(unittest.TestCase):

    def setUp(self):
        pdfFile = open('./tests/files/test.pdf', 'rb')
        self.pdfParser = PdfParser()
        self.lines = self.pdfParser.parse(pdfFile)
        pdfFile.close()

    def testFirstLine(self):
        print("\nAssert the line contain one suite of words")
        self.assertEqual(len(self.lines[0]), 1)

        print("\nAssert the suite of words is Text here")
        self.assertEqual(self.lines[0][0]['value'], 'Text here')

if __name__ == '__main__':
    unittest.main()
