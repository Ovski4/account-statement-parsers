import sys
import re
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class N26StatementParser:

    def __init__(self, lines):
        self.lines = lines

    def parse(self):
        transactions = []

        # for index, line in enumerate(self.lines):

        return transactions
