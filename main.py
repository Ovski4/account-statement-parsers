import sys
sys.path.append('modules')

from ccmparser import CCMParser
from pdfparser import PdfParser

pdfFile = open('files/releve-credit-mutuel-2017-05-31.pdf', 'rb')
lines = PdfParser().parse(pdfFile)
pdfFile.close()

ccmparser = CCMParser(lines)
transactions = ccmparser.parse()
