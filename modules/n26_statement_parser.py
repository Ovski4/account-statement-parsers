import sys
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class N26StatementParser:

    def __init__(self, lines):
        self.lines = lines
        self.account = None
        self.currentColumnBoundaries = None

    def setColumnBoundaries(self, line):
        self.currentColumnBoundaries = self.getColumnBoundaries(line)

    def parse(self):
        transactions = []

        for index, line in enumerate(self.lines):
            if self.isHeaderTableLine(line):
                self.setColumnBoundaries(line)
                continue

            if self.isAccountLine(line) and self.account is None:
                self.account = line[0]['value'] + ' N26'
                self.setAccountOnTransactions(transactions)
                continue

            if (self.currentColumnBoundaries is not None and self.isAmountLine(line)):
                transactions.append(self.extractTransaction(index, self.lines))
                continue

            if (self.currentColumnBoundaries is not None and self.isIncompleteAmountLine(index, self.lines)):
                transactions.append(self.extractTransactionFromMultipleLines(index, self.lines))

        return transactions

    def setAccountOnTransactions(self, transactions):
        for transaction in transactions:
            transaction['account'] = self.account

    def isHeaderTableLine(self, line):
        if (
            len(line) == 3 and
            line[0]['value'].lower() == 'description' and
            line[1]['value'].lower() == 'date de réservation' and
            line[2]['value'].lower() == 'montant'
        ):
            return True
        return False

    def isAccountLine(self, line):
        if (
            len(line) == 2 and
            line[1]['value'].lower() == 'émis le'
        ):
            return True
        return False

    def isIncompleteAmountLine(self, index, lines):
        if (index + 1 >= len(lines)):
            return False

        line = lines[index]
        nextLine = lines[index+1]
        if (
            len(line) == 2 and
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['date']) and
            self.linesAreWithinBoundaries(line[1], self.currentColumnBoundaries['amount']) and
            len(nextLine) == 1 and
            self.linesAreWithinBoundaries(nextLine[0], self.currentColumnBoundaries['description'])
        ):
            return True
        return False

    def getColumnBoundaries(self, line):
        boundaries = {}
        dictionnary = {
            'description': 'description',
            'date de réservation': 'date',
            'montant': 'amount'
        }

        for word in line:
            columnHeader = word['value'].lower()

            boundaries[dictionnary[columnHeader]] = {
                'x0': word['x0'],
                'x1': word['x1']
            }

        return boundaries


    def extractTransactionFromMultipleLines(self, lineIndex, lines):
        value = self.extractAmount(lines[lineIndex][1]['value'])
        label = lines[lineIndex+1][0]['value']

        transaction = {
            'account': self.account,
            'date': lines[lineIndex][0]['value'].replace('.', '/'),
            'label': label,
            'value': value
        }

        startIndex = lineIndex + 2
        for line in lines[startIndex:]:
            if self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['description']) and len(line) == 1:
                transaction['label'] = transaction.get('label') + ' - ' + line[0]['value']
            else:
                break

        return transaction

    def extractTransaction(self, lineIndex, lines):
        value = self.extractAmount(lines[lineIndex][2]['value'])

        transaction = {
            'account': self.account,
            'date': lines[lineIndex][1]['value'].replace('.', '/'),
            'label': lines[lineIndex][0]['value'],
            'value': value
        }

        startIndex = lineIndex + 2 # skip the first line (Mastercard . supermarche, etc)
        for line in lines[startIndex:]:
            if self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['description']) and len(line) == 1:
                transaction['label'] = transaction.get('label') + ' - ' + line[0]['value']
            else:
                break

        return transaction

    def extractAmount(self, value):
        value = value.replace('.', '').replace(',', '.')
        value = value[:-1] # get rid of the currency symbol

        return float(value)

    def isAmountLine(self, line):
        if (
            len(line) == 3 and
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['description']) and
            self.linesAreWithinBoundaries(line[1], self.currentColumnBoundaries['date']) and
            self.linesAreWithinBoundaries(line[2], self.currentColumnBoundaries['amount'])
        ):
            return True
        else:
            return False

    def linesAreWithinBoundaries(self, line1, line2):
        # allow a margin of 0.8
        if (
            (line1['x0']-line2['x0'] >= -0.8 and line2['x1']-line1['x1'] >= -0.8) or
            (line2['x0']-line1['x0'] >= -0.8 and line1['x1']-line2['x1'] >= -0.8)
        ):
            return True
        else:
            return False