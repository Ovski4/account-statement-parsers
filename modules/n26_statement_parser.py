import sys
import re
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class N26StatementParser:

    def __init__(self, lines):
        self.dateRegex  = re.compile(
            r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche), '
            r'(\d+)\. '
            r'(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)'
            r' (\d+)'
        )
        self.valueRegex = r'(-|\+)(\d+),(\d{2})€'
        self.months = {
            'janvier': '01',
            'février': '02',
            'mars': '03',
            'avril': '04',
            'mai': '05',
            'juin': '06',
            'juillet': '07',
            'août': '08',
            'septembre': '09',
            'octobre': '10',
            'novembre': '11',
            'décembre': '12',
        }
        self.lines = lines
        self.account = None
        # self.valueRightPosition = None
        self.currentDate = None
        self.currentTransactionLabel = None

    def parse(self):
        transactions = []

        for index, line in enumerate(self.lines):
            if index == 0:
                self.account = line[0]['value'] + ' N26'
                continue

            # if line[0]['value'] == 'Solde':
            #     self.valueRightPosition = line[0]['x1']
            #     continue

            if self.isDateLine(line):
                self.currentDate = self.extractDateFromLine(line)
                continue

            if self.currentDate is not None:

                if self.lineIsTransactionLabel(line):
                    self.currentTransactionLabel = line[0]['value']

                if self.lineHasTransactionValue(line) and self.currentTransactionLabel is not None:
                    transactions.append({
                        'account': self.account,
                        'date': self.currentDate,
                        'label': self.currentTransactionLabel,
                        'value': float(self.extractTransactionValue(line))
                    })
                    self.currentTransactionLabel = None

            if line[0]['value'].startswith('VIR DE M'):
                transactions[-1]['label'] = transactions[-1]['label'] + ' - ' + line[0]['value']

            if line[0]['value'] == 'Vue d’ensemble':
                break

        return transactions

    def isDateLine(self, line):
        return bool(re.match(self.dateRegex, line[0]['value']))

    def extractDateFromLine(self, line):
        matches = re.search(self.dateRegex, line[0]['value'])
        day = int(matches.group(2))
        month = matches.group(3)
        year = int(matches.group(4))

        return str(day) + '/' + self.months[month] + '/' + str(year)

    def lineIsTransactionLabel(self, line):
        return (line[0]['y0'] - line[0]['y1']) > 13

    def lineHasTransactionValue(self, line):
        for index, word in enumerate(line):
            if bool(re.match(self.valueRegex, word['value'])):
                return True

        return False

    def extractTransactionValue(self, line):
        for index, word in enumerate(line):
            if bool(re.match(self.valueRegex, word['value'])):
                matches = re.search(self.valueRegex, word['value'])
                sign = matches.group(1)
                integers = matches.group(2)
                decimals = matches.group(3)

                return float(sign + integers + '.' + decimals)