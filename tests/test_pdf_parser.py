from pdf_parser import PdfParser

def testFirstLine():

    pdfFile = open('./tests/files/test.pdf', 'rb')
    pdfParser = PdfParser()
    lines = pdfParser.parse(pdfFile)
    pdfFile.close()

    assert len(lines[0]) == 1
    assert lines[0][0]['value'] == 'Text here'

'''
readPdfFile builds its rows as (page, x0, bottom, x1, top, value), which is the shape groupLines
consumes. The coordinates below are the ones measured on a real fortuneo statement.
'''
def cell(value, x0, x1, top, bottom, page = 0):
    return (page, x0, bottom, x1, top, value)

def testCellsSharingATopAreOneLine():

    cells = [
        cell('11/08', 53.76, 73.78, 212.50, 204.50),
        cell('11/08/2026', 89.28, 129.31, 212.50, 204.50),
        cell('13,40', 443.28, 463.30, 212.50, 204.50)
    ]

    lines = PdfParser().groupLines(cells)

    assert len(lines) == 1
    assert [word['value'] for word in lines[0]] == ['11/08', '11/08/2026', '13,40']

def testCellsFurtherApartThanTheThresholdAreSeparateLines():

    # 212.50 and 201.94 are 10.56 apart, past the 10 point threshold
    cells = [
        cell('13,40', 443.28, 463.30, 212.50, 204.50),
        cell('1,90', 447.62, 463.22, 201.94, 193.94)
    ]

    lines = PdfParser().groupLines(cells)

    assert len(lines) == 2

def testAShortCellBetweenTwoRowsDoesNotMergeThem():

    # one character of the vertical text fortuneo prints down the left margin, sitting between
    # two transaction rows. it is half as tall as a row and all but shares the first row's
    # bottom, 204.59 against 204.50, so it sorts ahead of that row while its top, 208.92, falls
    # in the gap between the two rows: 3.58 below the first and 6.98 above the second.
    cells = [
        cell('R', 29.34, 35.34, 208.92, 204.59),
        cell('11/08', 53.76, 73.78, 212.50, 204.50),
        cell('13,40', 443.28, 463.30, 212.50, 204.50),
        cell('A', 29.34, 35.34, 204.59, 200.59),
        cell('P', 29.34, 35.34, 200.59, 196.58),
        cell('11/08', 53.76, 73.78, 201.94, 193.94),
        cell('1,90', 447.62, 463.22, 201.94, 193.94)
    ]

    lines = PdfParser().groupLines(cells)

    # anchoring the group on its first cell would accept both rows against that margin character
    # and return all seven cells as a single line, hiding two transactions
    assert len(lines) == 2
    assert [word['value'] for word in lines[0]] == ['R', '11/08', '13,40', 'A']
    assert [word['value'] for word in lines[1]] == ['P', '11/08', '1,90']

def testNoLineSpansMoreThanTheThreshold():

    pdfFile = open('./tests/files/test.pdf', 'rb')
    lines = PdfParser().parse(pdfFile)
    pdfFile.close()

    for line in lines:
        tops = [word['y0'] for word in line]
        assert max(tops) - min(tops) <= PdfParser.LINE_THRESHOLD
