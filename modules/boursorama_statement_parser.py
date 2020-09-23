import sys
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class BoursoramaStatementParser:

    def __init__(self, lines):
        self.lines = lines

    def parse(self):
        transactions = []

        return transactions
