import sys
sys.path.append('./modules')
from linereader import LineReader
from pdfparser import PdfParser

class CCMParser:

    def __init__(self, lines):
        self.lines = lines
        self.currentAccount = None
        self.currentColumnBoundaries = None
        self.lastHeaderTableLineIndex = None
        self.data = []

    def setColumnBoundaries(self, line):
        self.currentColumnBoundaries = self.getColumnBoundaries(line)

    def parse(self):
        transactions = []

        # remove vertical line on the left. Sometimes 2 characters on the same line
        for line in self.lines[:]:
            for word in line[:]:
                if self.isVerticalLeftSideWord(word):
                    line.remove(word)
            if len(line) == 0:
                self.lines.remove(line)

        for index, line in enumerate(self.lines):
            if self.isAccountNameLine(index, self.lines):
                self.currentAccount = self.extractAccountName(line)
                continue

            if self.isHeaderTableLine(line):
                self.setColumnBoundaries(line)
                self.lastHeaderTableLineIndex = index
                continue

            if (self.currentAccount is not None and self.currentColumnBoundaries is not None):
                if self.isDebitLine(line):
                    transactions.append(self.extractTransaction(index, self.lines, 'debit'))
                elif self.isCreditLine(line):
                    transactions.append(self.extractTransaction(index, self.lines, 'credit'))
                elif self.isFirstAccountOnPageWithOnlyOperationLine(index, self.lines):
                    listLength = len(transactions)
                    lastTransaction = transactions[listLength-1]
                    transactions[listLength-1]['label'] = lastTransaction.get('label') + ' ' + line[0]['value']

        return transactions

    def isHeaderTableLine(self, line):
        if (
            len(line) == 5 and
            line[0]['value'].lower() == 'date' and
            line[1]['value'].lower() == 'date valeur' and
            line[2]['value'].lower() == 'opération' and
            line[3]['value'].lower() == 'débit euros' and
            line[4]['value'].lower() == 'crédit euros'
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
            len(line) == 4 and
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
            len(line) == 4 and
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['date']) and
            self.linesAreWithinBoundaries(line[1], self.currentColumnBoundaries['date_valeur']) and
            self.linesAreWithinBoundaries(line[2], self.currentColumnBoundaries['operation']) and
            self.linesAreWithinBoundaries(line[3], self.currentColumnBoundaries['credit'])
        ):
            return True
        else:
            return False

    def isFirstAccountOnPageWithOnlyOperationLine(self, lineIndex, lines):
        if (
            len(lines[lineIndex]) == 1 and
            self.linesAreWithinBoundaries(lines[lineIndex][0], self.currentColumnBoundaries['operation']) and
            self.lastHeaderTableLineIndex == lineIndex-1
        ):
            return True
        else:
            return False

    def isVerticalLeftSideWord(self, word):
        if word.get('x0') < 10 and word.get('x1') < 15:
            return True

    def extractAccountName(self, line):
        # line[0] as the account name line contains always only one item
        index = line[0]['value'].index(' en euros')
        return line[0]['value'][:index]

    def extractTransaction(self, lineIndex, lines, transactionType):

        value = float(
          lines[lineIndex][3]['value']
          .replace('.', '')
          .replace(',', '.')
        )

        transaction = {
            'account': self.currentAccount,
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
        # allow a margin of 0.09
        if (
            (line1['x0']-line2['x0'] >= -0.09 and line2['x1']-line1['x1'] >= -0.09) or
            (line2['x0']-line1['x0'] >= -0.09 and line1['x1']-line2['x1'] >= -0.09)
        ):
            return True
        else:
            return False

    def getColumnBoundaries(self, line):
        boundaries = {}
        dictionnary = {
            'date': 'date',
            'date valeur': 'date_valeur',
            'opération': 'operation',
            'débit euros': 'debit',
            'crédit euros': 'credit'
        }

        for word in line:
            margin = 0
            columnHeader = word['value'].lower()
            if (columnHeader == 'opération'):
                margin = 13.2

            boundaries[dictionnary[columnHeader]] = {
                'x0': round(word['x0'] - margin, 2),
                'x1': word['x1']
            }

        return boundaries
