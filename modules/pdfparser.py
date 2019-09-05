from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine
from pdfminer.pdfpage import PDFPage

class PdfParser:
    LINE_THRESHOLD = 10

    def parse(self, PDFfile):
        lines = self.groupLines(self.readPdfFile(PDFfile))
        return list(map(lambda line: sorted(line, key = lambda x: x['x0']), lines))

    def readPdfFile(self, PDFfile):
        parser = PDFParser(PDFfile)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(char_margin=0.4)

        device = PDFPageDetailedAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
            device.get_result()

        return device.cells

    def groupLines(self, cells):
        lines = [[]]

        for cell in cells:
            _, x0, y1, x1, y0, value = cell

            if lines[-1] and abs(lines[-1][0]['y0'] - y0) > PdfParser.LINE_THRESHOLD:
                lines.append([])

            lines[-1].append({'value': value, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1})

        return lines

class PDFPageDetailedAggregator(PDFPageAggregator):
    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFPageAggregator.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)
        self.cells = []
        self.page_number = 0

    def receive_layout(self, ltpage):
        def render(item, page_number):
            if isinstance(item, LTPage) or isinstance(item, LTTextBox):
                for child in item:
                    render(child, page_number)
            elif isinstance(item, LTTextLine):
                child_str = ''
                for child in item:
                    if isinstance(child, (LTChar, LTAnno)):
                        child_str += child.get_text()
                child_str = ' '.join(child_str.split()).strip()
                if child_str:
                    x0, y0, x1, y1 = item.bbox
                    row = (page_number, round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2), child_str)
                    self.cells.append(row)
                for child in item:
                    render(child, page_number)
            return

        render(ltpage, self.page_number)

        self.page_number += 1
        self.cells = sorted(self.cells, key = lambda x: (x[0], -x[2]))
        self.result = ltpage
