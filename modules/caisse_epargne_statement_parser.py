import sys
import re
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class CaisseEpargneStatementParser:

    def __init__(self, lines):
        self.lines = lines
        self.currentAccount = None
        self.currentColumnBoundaries = None
        self.lastHeaderTableLineIndex = None
        self.statementYear = None
        self.data = []

    def setColumnBoundaries(self, line):
        self.currentColumnBoundaries = self.getColumnBoundaries(line)

    def parse(self):
        transactions = []

        # remove left side lines
        for line in self.lines[:]:
            for word in line[:]:
                if word['x0'] < 30:
                    line.remove(word)
            if len(line) == 0:
                self.lines.remove(line)

        for index, line in enumerate(self.lines):
            if self.isDateLine(line):
                self.statementYear = self.getStatementYear(line)

            if self.isHeaderTableLine(line):
                self.currentAccount = self.extractAccountName(self.lines[index-1])
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
            len(line) == 4 and
            line[0]['value'].lower() == 'date' and
            line[1]['value'].lower() == 'détail des opérations en euros' and
            line[2]['value'].lower() == 'débit' and
            line[3]['value'].lower() == 'crédit'
        ):
            return True
        return False

    def isDateLine(self, line):
        return bool(re.match(r"^au\s\d+/\d+/\d+\s-\sN°\s\d+$", line[0]['value']))

    def getStatementYear(self, line):
        return re.search(r'^au\s\d+/\d+/(\d+)\s-\sN°\s\d+$', line[0]['value']).group(1)

    def isDebitLine(self, line):
        # we just check the first one
        for index, word in enumerate(line[1:(len(line)-1)]):
            if index >= 2:
                break
            elif not self.linesAreWithinBoundaries(word, self.currentColumnBoundaries['détail des opérations en euros']):
                return False

        if (
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['date']) and
            bool(re.match(r"^\d+/\d+$", line[0]['value'])) and
            self.linesAreWithinBoundaries(line[len(line)-1], self.currentColumnBoundaries['débit'])
        ):
            return True
        else:
            return False

    def isCreditLine(self, line):
        for index, word in enumerate(line[1:(len(line)-1)]):
            if index >= 2:
                break
            elif not self.linesAreWithinBoundaries(word, self.currentColumnBoundaries['détail des opérations en euros']):
                return False

        if (
            self.linesAreWithinBoundaries(line[0], self.currentColumnBoundaries['date']) and
            bool(re.match(r"^\d+/\d+$", line[0]['value'])) and
            self.linesAreWithinBoundaries(line[len(line)-1], self.currentColumnBoundaries['crédit'])
        ):
            return True
        else:
            return False

    def isFirstAccountOnPageWithOnlyOperationLine(self, lineIndex, lines):
        if (
            len(lines[lineIndex]) == 1 and
            self.linesAreWithinBoundaries(lines[lineIndex][0], self.currentColumnBoundaries['détail des opérations en euros']) and
            self.lastHeaderTableLineIndex == lineIndex-1
        ):
            return True
        else:
            return False

    def extractAccountName(self, line):
        if (len(line) > 2):
            raise Exception('Unexpected pdf format. The line above the header line contains multiple lines')
        elif (len(line) == 2) and line[1]['value'].endswith(' (suite)'):
            return self.currentAccount
        else:
            return line[0]['value']

    def extractTransaction(self, lineIndex, lines, transactionType):
        lastLine = len(lines[lineIndex])-1
        value = float(
            lines[lineIndex][lastLine]['value']
            .replace(' ', '')
            .replace(',', '.')
        )

        label = ''
        for index, word in enumerate(lines[lineIndex][1:lastLine]):
            if index == 0:
                label = word['value']
            else:
                label = label + ' ' + word['value']

        transaction = {
            'account': self.currentAccount,
            'date': lines[lineIndex][0]['value'] + '/' +  self.statementYear,
            'label': label,
            'value': value if transactionType == 'credit' else -value
        }

        startIndex = lineIndex + 1
        for line in lines[startIndex:]:
            if (
                self.linesAreWithinBoundaries(
                    line[0],
                    self.currentColumnBoundaries['détail des opérations en euros']
                )
            ):
                label = ''
                for index, word in enumerate(line):
                    if (
                        ('Frais bancaires et cotisations :' in word['value']) or
                        ('Paiements chèques' in word['value']) or 
                        ('Paiements carte bancaire' in word['value']) or 
                        ('Retraits carte bancaire' in word['value']) or 
                        ('Prélèvements' in word['value']) or 
                        ('NOUVEAU SOLDE CREDITEUR' in word['value']) or 
                        ("Les lignes d'opérations correspondant à des frais et cotisations commencent par une étoile" in word['value'])
                    ):
                        break
                    if index == 0:
                        label = word['value']
                    else:
                        label = label + ' ' + word['value']
                transaction['label'] = transaction.get('label') + ' ' + label
            else:
                break

        transaction['label'] = self.cleanLabel(transaction.get('label'))

        return transaction

    def cleanLabel(self, label):
        label = label.split('-Réf.')[0].strip()

        if bool(re.match(r"^.*\s+FACT\s\d{6}$", label)):
            label = re.search(r"^(.*)\s+FACT\s\d{6}$", label).group(1)

        return label

    def linesAreWithinBoundaries(self, line1, line2):
        if (
                (line1['x0']-line2['x0'] >= -2.7 and line2['x1']-line1['x1'] >= -2.7) or
                (line2['x0']-line1['x0'] >= -2.7 and line1['x1']-line2['x1'] >= -2.7)
        ):
            return True
        else:
            return False

    def getColumnBoundaries(self, line):
        boundaries = {}

        for word in line:
            columnHeader = word['value'].lower()
            boundaries[columnHeader] = {
                'x0': word['x0'],
                'x1': word['x1']
            }

        return boundaries
