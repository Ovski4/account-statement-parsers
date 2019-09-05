import sys
sys.path.append('modules')

from pdfparser import PdfParser

pdfFile = open('releve-credit-mutuel-2014-06-02.pdf', 'rb')
lines = PdfParser().parse(pdfFile)
for line in lines:
    print(line)
pdfFile.close()
