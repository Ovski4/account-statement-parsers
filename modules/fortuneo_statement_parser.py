import sys
import re
import copy
sys.path.append('./modules')
from line_reader import LineReader
from pdf_parser import PdfParser

class FortuneoStatementParser:

    MONTHS = {
        'janvier': 1,
        'février': 2,
        'mars': 3,
        'avril': 4,
        'mai': 5,
        'juin': 6,
        'juillet': 7,
        'août': 8,
        'septembre': 9,
        'octobre': 10,
        'novembre': 11,
        'décembre': 12
    }

    '''
    Labels that must never be glued to the previous transaction by the multi line label loop.
    '''
    LABEL_STOP_WORDS = [
        'TOTAL DES OPÉRATIONS',
        'NOUVEAU SOLDE',
        'ANCIEN SOLDE',
        'Garantie de vos dépôts',
        'Total de vos services et frais bancaires',
        'À reporter',
        'Report'
    ]

    def __init__(self, lines):
        # the left margin pre pass mutates the lines, work on our own copy so that a fixture
        # can be parsed more than once
        self.lines = copy.deepcopy(lines)
        self.account = None
        self.statementMonth = None
        self.statementYear = None
        self.headerTableSeen = False
        '''
        Fortuneo right aligns the amounts far to the right of their column header, and left aligns
        the labels far to the left of theirs, so the boundaries cannot be read from the header
        line the way the other pdf parsers do it. They are hardcoded, as in the boursorama parser.
        '''
        self.columnBoundaries = {
            'date': {
                'x0': 45,
                'x1': 80
            },
            'date_valeur': {
                'x0': 82,
                'x1': 132
            },
            'label': {
                'x0': 133,
                'x1': 400
            },
            'debit': {
                'x0': 400,
                'x1': 470
            },
            'credit': {
                'x0': 500,
                'x1': 560
            }
        }

    def parse(self):
        transactions = []

        self.removeLeftMarginWords()

        for index, line in enumerate(self.lines):
            if self.account is None:
                self.setAccountFromLine(line)

            if self.statementYear is None:
                self.setStatementPeriodFromLine(line)

            if self.isHeaderTableLine(line):
                self.headerTableSeen = True
                continue

            if not self.headerTableSeen:
                continue

            if self.isDebitLine(line):
                transactions.append(self.extractTransaction(index, self.lines, 'debit'))
            elif self.isCreditLine(line):
                transactions.append(self.extractTransaction(index, self.lines, 'credit'))

        if self.account is None:
            raise Exception(
                'Could not find the IBAN on the statement. The account block is missing or its '
                'layout changed, transactions would be returned without an account.'
            )

        self.validateAgainstStatementBalance(transactions)

        return transactions

    '''
    The vertical text printed on the left margin comes out as one cell per character and some of
    those rows hold exactly 4 cells, which is the shape of a transaction row.
    '''
    def removeLeftMarginWords(self):
        for line in self.lines[:]:
            for word in line[:]:
                if word['x1'] < 40:
                    line.remove(word)
            if len(line) == 0:
                self.lines.remove(line)

    def wordIsWithinBoundaries(self, word, boundary):
        return word['x0'] >= boundary['x0'] and word['x1'] <= boundary['x1']

    def isHeaderTableLine(self, line):
        if (
            len(line) == 5 and
            line[0]['value'].lower() == 'date' and
            line[1]['value'].lower() == 'date de valeur' and
            line[2]['value'].lower() == 'opération' and
            line[3]['value'].lower() == 'débit' and
            line[4]['value'].lower() == 'crédit'
        ):
            return True
        return False

    def isDateWord(self, word):
        return (
            self.wordIsWithinBoundaries(word, self.columnBoundaries['date']) and
            bool(re.match(r'^\d{1,2}/\d{2}$', word['value']))
        )

    def isDateValeurWord(self, word):
        return (
            self.wordIsWithinBoundaries(word, self.columnBoundaries['date_valeur']) and
            bool(re.match(r'^\d{1,2}/\d{2}/\d{4}$', word['value']))
        )

    def isTransactionLine(self, line, amountColumn):
        if len(line) != 4:
            return False

        if (
            self.isDateWord(line[0]) and
            self.isDateValeurWord(line[1]) and
            self.wordIsWithinBoundaries(line[2], self.columnBoundaries['label']) and
            self.wordIsWithinBoundaries(line[3], self.columnBoundaries[amountColumn])
        ):
            return True

        return False

    def isDebitLine(self, line):
        return self.isTransactionLine(line, 'debit')

    def isCreditLine(self, line):
        return self.isTransactionLine(line, 'credit')

    def isLabelStopWord(self, value):
        for stopWord in FortuneoStatementParser.LABEL_STOP_WORDS:
            if value.startswith(stopWord):
                return True
        return False

    def extractAmount(self, value):
        value = re.sub(r'\s', '', value)
        value = value.replace('€', '').replace('.', '').replace(',', '.')

        return float(value)

    '''
    pdfminer returns the iban and the bic in a single cell:
    'IBAN FR76 3000 1000 0100 0000 0000 123 BIC FTNOFRP1XXX'
    '''
    def extractIban(self, value):
        matches = re.search(r'IBAN\s+([A-Z]{2}\d{2}(?:\s[A-Z0-9]{1,4})+)\s+BIC', value)

        if matches is None:
            matches = re.search(r'\b([A-Z]{2}\d{2}(?:\s[A-Z0-9]{1,4}){4,7})\b', value)

        if matches is None:
            return None

        iban = matches.group(1)
        if not self.isValidIban(iban):
            return None

        return iban

    def isValidIban(self, iban):
        compactIban = iban.replace(' ', '')

        return (
            bool(re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', compactIban)) and
            len(compactIban) >= 15 and
            len(compactIban) <= 34
        )

    def setAccountFromLine(self, line):
        for word in line:
            iban = self.extractIban(word['value'])
            if iban is not None:
                self.account = iban
                return

    def setStatementPeriodFromLine(self, line):
        for word in line:
            matches = re.search(r'Arrêté au \d{1,2}\s+(\S+)\s+(\d{4})', word['value'])
            if matches is None:
                continue

            month = FortuneoStatementParser.MONTHS.get(matches.group(1).lower())
            if month is None:
                continue

            self.statementMonth = month
            self.statementYear = int(matches.group(2))
            return

    '''
    The date column holds a day and a month only. The statement covers the month it is dated in,
    so an operation dated in a later month belongs to the previous year (a december operation
    listed on a january statement).
    '''
    def getTransactionYear(self, operationDate, dateValeur):
        month = int(operationDate.split('/')[1])

        if self.statementYear is not None:
            year = self.statementYear
            statementMonth = self.statementMonth
        else:
            # fall back on the value date of the row itself
            year = int(dateValeur.split('/')[2])
            statementMonth = int(dateValeur.split('/')[1])

        if month > statementMonth:
            year = year - 1

        return str(year)

    def formatDate(self, operationDate, dateValeur):
        day, month = operationDate.split('/')

        return day.zfill(2) + '/' + month.zfill(2) + '/' + self.getTransactionYear(operationDate, dateValeur)

    def extractTransaction(self, lineIndex, lines, transactionType):
        value = self.extractAmount(lines[lineIndex][3]['value'])

        transaction = {
            'account': self.account,
            'date': self.formatDate(lines[lineIndex][0]['value'], lines[lineIndex][1]['value']),
            'label': lines[lineIndex][2]['value'],
            'value': value if transactionType == 'credit' else -value
        }

        startIndex = lineIndex + 1
        for line in lines[startIndex:]:
            if (
                len(line) == 1 and
                self.wordIsWithinBoundaries(line[0], self.columnBoundaries['label']) and
                not self.isLabelStopWord(line[0]['value'])
            ):
                transaction['label'] = transaction.get('label') + ' ' + line[0]['value']
            else:
                break

        return transaction

    def isBalanceLine(self, line, label):
        return line[0]['value'].startswith(label)

    '''
    The balance is printed unsigned, the CRÉDITEUR / DÉBITEUR keyword carries the sign.
    '''
    def extractBalance(self, line):
        balance = self.extractAmount(line[len(line)-1]['value'])

        for word in line:
            if 'DÉBITEUR' in word['value'].upper():
                return -balance

        return balance

    def extractOperationTotals(self, line):
        debitTotal = 0.0
        creditTotal = 0.0

        for word in line[1:]:
            if self.wordIsWithinBoundaries(word, self.columnBoundaries['debit']):
                debitTotal = self.extractAmount(word['value'])
            elif self.wordIsWithinBoundaries(word, self.columnBoundaries['credit']):
                creditTotal = self.extractAmount(word['value'])

        return debitTotal, creditTotal

    def findLastLineStartingWith(self, label):
        found = None

        for line in self.lines:
            if self.isBalanceLine(line, label):
                found = line

        return found

    def amountsMatch(self, computed, expected):
        return abs(round(computed, 2) - round(expected, 2)) < 0.005

    '''
    A debit and a credit row only differ by the x position of the amount, so a column drifting a
    few points silently flips a sign instead of raising. The statement states its own totals, use
    them to turn that into a loud failure.
    '''
    def validateAgainstStatementBalance(self, transactions):
        # on a multi page statement only the last occurrence of each row is the final one
        ancienSoldeLine = self.findLastLineStartingWith('ANCIEN SOLDE')
        nouveauSoldeLine = self.findLastLineStartingWith('NOUVEAU SOLDE')
        totalLine = self.findLastLineStartingWith('TOTAL DES OPÉRATIONS')

        if ancienSoldeLine is None or nouveauSoldeLine is None or totalLine is None:
            raise Exception(
                'Could not find the ANCIEN SOLDE, TOTAL DES OPÉRATIONS and NOUVEAU SOLDE rows '
                'needed to check the parsed transactions. The statement layout changed, the '
                'transactions cannot be trusted.'
            )

        ancienSolde = self.extractBalance(ancienSoldeLine)
        nouveauSolde = self.extractBalance(nouveauSoldeLine)
        debitTotal, creditTotal = self.extractOperationTotals(totalLine)

        values = list(map(lambda transaction: transaction['value'], transactions))
        computed = sum(values)
        expected = nouveauSolde - ancienSolde

        if not self.amountsMatch(computed, expected):
            raise Exception(
                'Parsed transactions do not match the statement balance. Expected %.2f '
                '(nouveau solde %.2f - ancien solde %.2f), got %.2f from %d transactions '
                '(difference: %.2f). A transaction was probably missed, duplicated, or '
                'classified as debit instead of credit.'
                % (expected, nouveauSolde, ancienSolde, computed, len(transactions), computed - expected)
            )

        computedDebit = sum([value for value in values if value < 0])
        if not self.amountsMatch(computedDebit, -debitTotal):
            raise Exception(
                'Parsed debits do not match the statement total. Expected %.2f, got %.2f from %d '
                'transactions (difference: %.2f). An amount was probably read in the wrong column.'
                % (-debitTotal, computedDebit, len(transactions), computedDebit + debitTotal)
            )

        computedCredit = sum([value for value in values if value > 0])
        if not self.amountsMatch(computedCredit, creditTotal):
            raise Exception(
                'Parsed credits do not match the statement total. Expected %.2f, got %.2f from %d '
                'transactions (difference: %.2f). An amount was probably read in the wrong column.'
                % (creditTotal, computedCredit, len(transactions), computedCredit - creditTotal)
            )
