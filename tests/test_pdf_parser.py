from pdf_parser import PdfParser

def testFirstLine():

    pdfFile = open('./tests/files/test.pdf', 'rb')
    pdfParser = PdfParser()
    lines = pdfParser.parse(pdfFile)
    pdfFile.close()

    assert len(lines[0]) == 1
    assert lines[0][0]['value'] == 'Text here'
