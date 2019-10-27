import sys
sys.path.append('./modules')
from linereader import LineReader
from pdfparser import PdfParser

class CCMParser:

    def __init__(self, lines):
        self.lines = lines
        self.currentAccount = None
        self.currentColumnBoundaries = None
        self.data = []

    def setColumnBoundaries(self, line):
        self.currentColumnBoundaries = self.getColumnBoundaries(line)

    def parse(self):
        transactions = {}

        for index, line in enumerate(self.lines):

            if self.isAccountNameLine(index, self.lines):
                self.currentAccount = self.extractAccountName(line)
                if self.currentAccount not in transactions:
                    transactions[self.currentAccount] = []
                continue

            if self.isHeaderTableLine(line):
                self.setColumnBoundaries(line)
                continue

            if (self.currentAccount is not None and self.currentColumnBoundaries is not None):
                if self.isDebitLine(line):
                    transactions[self.currentAccount].append(self.extractTransaction(index, self.lines, 'debit'))
                elif self.isCreditLine(line):
                    transactions[self.currentAccount].append(self.extractTransaction(index, self.lines, 'credit'))

        return transactions

    def isHeaderTableLine(self, line):
        if (
            len(line) == 5 and
            line[0]['value'] == 'Date' and
            line[1]['value'] == 'Date valeur' and
            line[2]['value'] == 'Opération' and
            line[3]['value'] == 'Débit euros' and
            line[4]['value'] == 'Crédit euros'
        ):
            return True
        return False

    def isAccountNameLine(self, lineIndex, lines):
        line1Reader = LineReader(self.lines[lineIndex])
        if line1Reader.contains('en euros'):
            line2Reader = LineReader(self.lines[lineIndex + 1])
            if line2Reader.contains('TITULAIRE(S)'):
                return True
            else:
                return False
        else:
            return False

    def isDebitLine(self, line):
        # todo add regexes
        if (
            len(line) >= 4 and
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['date']) and
            self.linesAreWithinBoundaries(line[1], self.currentColumnBoundaries['date_valeur']) and
            self.linesAreWithinBoundaries(line[2], self.currentColumnBoundaries['operation']) and
            self.linesAreWithinBoundaries(line[3], self.currentColumnBoundaries['debit'])
        ):
            return True
        else:
            return False

    def isCreditLine(self, line):
        # todo add regexes
        if (
            len(line) >= 4 and
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['date']) and
            self.linesAreWithinBoundaries(line[1], self.currentColumnBoundaries['date_valeur']) and
            self.linesAreWithinBoundaries(line[2], self.currentColumnBoundaries['operation']) and
            self.linesAreWithinBoundaries(line[3], self.currentColumnBoundaries['credit'])
        ):
            return True
        else:
            return False

    def extractAccountName(self, line):
        # index 0 as the account name line contains always only one item
        return line[0]['value'][:-len(' en euros')]

    def extractTransaction(self, lineIndex, lines, transactionType):

        value = float(
          lines[lineIndex][3]['value']
          .replace('.', '')
          .replace(',', '.')
        )

        transaction = {
            'date': lines[lineIndex][0]['value'],
            'label': lines[lineIndex][2]['value'],
            'value': value if transactionType == 'credit' else -value
        }

        startIndex = lineIndex + 1
        for line in lines[startIndex:]:
            if self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['operation']) and len(line) == 1:
                transaction['label'] = transaction.get('label') + ' ' + line[0]['value']
            else:
                break

        return transaction

    def linesAreWithinBoundaries(self, line1, line2):
        # allow a margin of 0.05
        if (
            (line1['x0']-line2['x0'] >= -0.05 and line2['x1']-line1['x1'] >= -0.05) or
            (line2['x0']-line1['x0'] >= -0.05 and line1['x1']-line2['x1'] >= -0.05)
        ):
            return True
        else:
            return False

    def getColumnBoundaries(self, line):
        boundaries = {}
        dictionnary = {
            'Date': 'date',
            'Date valeur': 'date_valeur',
            'Opération': 'operation',
            'Débit euros': 'debit',
            'Crédit euros': 'credit'
        }

        for word in line:
            boundaries[dictionnary[word['value']]] = {
                'x0': word['x0'],
                'x1': word['x1']
            }

        return boundaries
