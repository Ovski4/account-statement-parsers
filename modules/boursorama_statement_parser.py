import sys
import re
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class BoursoramaStatementParser:

    def __init__(self, lines):
        self.lines = lines
        self.account = None
        self.columnBoundaries = {
            'label': {
                'x0': 82,
                'x1': 275
            },
            'date': {
                'x0': 32,
                'x1': 81
            },
            'debit': {
                'x0': 310,
                'x1': 446
            },
            'credit': {
                'x0': 453,
                'x1': 536
            }
        }

    def parse(self):
        transactions = []

        for index, line in enumerate(self.lines):
            if self.isBankAccountLine(line):
                self.account = self.extractBankAccount(line)
                continue

            if self.isDebitLine(line):
                transactions.append(self.extractTransaction(index, self.lines, 'debit'))
                continue

            if self.isCreditLine(line):
                transactions.append(self.extractTransaction(index, self.lines, 'credit'))

        return transactions

    # def isBankBalanceLine(self, line):
    #     if len(line) != 3:
    #         return False

    #     if (line[0]['value'] != 'SOLDE AU :'):
    #         return False

    #     return True

    def isLabelWord(self, word):
        return self.wordIsWithinBoundaries(word, self.columnBoundaries['label'])

    def isDateWord(self, word):
        return self.wordIsWithinBoundaries(word, self.columnBoundaries['date']) and self.isDate(word['value'])

    def isDebitWord(self, word):
        return self.wordIsWithinBoundaries(word, self.columnBoundaries['debit'])

    def isCreditWord(self, word): 
        return self.wordIsWithinBoundaries(word, self.columnBoundaries['credit'])

    def wordIsWithinBoundaries(self, word, boundary):
        return word['x0'] >= boundary['x0'] and word['x1'] <= boundary['x1']

    def isDebitLine(self, line):
        if len(line) != 4:
            return False

        if self.isDateWord(line[0]) and self.isLabelWord(line[1]) and self.isDebitWord(line[3]):
            return True

        return False

    def isCreditLine(self, line):
        if len(line) != 4:
            return False

        if self.isDateWord(line[0]) and self.isLabelWord(line[1]) and self.isCreditWord(line[3]):
            return True

        return False

    def isDate(self, value):
        dateRegex = r'\d{1,2}\/\d{2}\/\d{4}'
        return bool(re.match(dateRegex, value))

    def isDateWithoutLeadingZero(self, value):
        dateRegex = r'\d{1}\/\d{2}\/\d{4}'
        return bool(re.match(dateRegex, value))

    def isBankAccountLine(self, line):
        if len(line) != 11:
            return False

        if (self.isDate(line[0]['value']) and
            line[1]['value'].isdigit() and
            line[2]['value'].isdigit() and
            line[3]['value'].isdigit() and
            line[4]['value'].isdigit() and
            (not line[5]['value'].isdigit())):
            return True

        return False

    def extractBankAccount(self, line):
        return line[1]['value'] + ' ' + line[2]['value'] + ' ' + line[3]['value'] + ' ' + line[4]['value']

    def extractTransaction(self, lineIndex, lines, transactionType):

        value = float(
          lines[lineIndex][3]['value']
          .replace('.', '')
          .replace(',', '.')
        )

        date = lines[lineIndex][0]['value']
        if self.isDateWithoutLeadingZero(date):
            date = '0' + date

        transaction = {
            'account': self.account,
            'date': date,
            'label': lines[lineIndex][1]['value'],
            'value': value if transactionType == 'credit' else -value
        }

        startIndex = lineIndex + 1
        for line in lines[startIndex:]:
            if len(line) == 1 and self.isLabelWord(line[0]):
                transaction['label'] = transaction.get('label') + ' - ' + line[0]['value']
            else:
                break

        return transaction
