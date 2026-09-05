import json
import pytest

from fortuneo_statement_parser import FortuneoStatementParser

from releve_fortuneo_1 import fortuneo_lines_1

'''
Page 2 of a real statement is translated this many points to the right of page 1, header row
included. Measured on the august 2026 statement, where every header cell moved by exactly that.
'''
SECOND_PAGE_OFFSET = 4.56

'''
Helpers building synthetic statements. The sample statement holds credits only, so the debit
column x range and the balance self check can only be covered this way. The x coordinates are
the ones measured on the real statement, the y ones are irrelevant to this parser. An offset
places a line on a page laid out further right, the way page 2 is.
'''
def word(value, x0, x1, y0 = 500.0, offset = 0.0):
    return {'value': value, 'x0': x0 + offset, 'y0': y0, 'x1': x1 + offset, 'y1': y0 + 9.0}

def headerTableLine(offset = 0.0):
    return [
        word('Date', 56.88, 74.22, offset = offset),
        word('Date de Valeur', 83.76, 139.34, offset = offset),
        word('Opération', 236.16, 273.94, offset = offset),
        word('Débit', 407.28, 427.28, offset = offset),
        word('Crédit', 495.36, 518.47, offset = offset)
    ]

def transactionLine(date, dateValeur, label, amount, column, offset = 0.0):
    boundaries = {'debit': (447.6, 463.17), 'credit': (532.08, 552.1)}
    x0, x1 = boundaries[column]

    return [
        word(date, 53.76, 73.78, offset = offset),
        word(dateValeur, 89.28, 129.31, offset = offset),
        word(label, 135.84, 278.09, offset = offset),
        word(amount, x0, x1, offset = offset)
    ]

def buildStatement(
    transactionLines,
    ancienSolde = '0,00 €',
    nouveauSolde = '0,00 €',
    debitTotal = '0,00',
    creditTotal = '0,00',
    soldeKeyword = 'CRÉDITEUR',
    withIban = True,
    withBalanceRows = True,
    secondPageTransactionLines = None
):
    lines = []

    if withIban:
        lines.append([word('IBAN FR76 3000 1000 0100 0000 0000 123 BIC FTNOFRP1XXX', 58.08, 303.75)])

    lines.append([word('Arrêté au 31 juillet 2026', 263.52, 386.41)])
    lines.append(headerTableLine())

    if withBalanceRows:
        lines.append([word('ANCIEN SOLDE', 53.76, 121.76), word(ancienSolde, 528.96, 549.36)])

    lines.extend(transactionLines)

    # a second page repeats the header row, at its own offset
    closingOffset = 0.0

    if secondPageTransactionLines is not None:
        closingOffset = SECOND_PAGE_OFFSET
        lines.append(headerTableLine(offset = closingOffset))
        lines.extend(secondPageTransactionLines)

    # the closing rows end the statement, so they sit on the last page and carry its offset
    if withBalanceRows:
        lines.append([
            word('TOTAL DES OPÉRATIONS DU RELEVÉ', 51.12, 205.63, offset = closingOffset),
            word(debitTotal, 447.6, 463.17, offset = closingOffset),
            word(creditTotal, 521.28, 552.42, offset = closingOffset)
        ])
        lines.append([
            word('NOUVEAU SOLDE', 53.76, 132.27, offset = closingOffset),
            word(soldeKeyword, 135.36, 187.86, offset = closingOffset),
            word('AU 31 JUILLET 2026', 190.56, 277.59, offset = closingOffset),
            word(nouveauSolde, 511.2, 549.36, offset = closingOffset)
        ])

    return lines


def testParse():

    parser = FortuneoStatementParser(fortuneo_lines_1)
    transactions = parser.parse()
    with open('./tests/files/expected-results-fortuneo-1.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

def testParsingTwiceGivesTheSameResult():

    # the left margin pre pass must not mutate the fixture it was given
    first = FortuneoStatementParser(fortuneo_lines_1).parse()
    second = FortuneoStatementParser(fortuneo_lines_1).parse()
    assert first == second

def testParseDebitTransaction():

    lines = buildStatement(
        [transactionLine('12/07', '12/07/2026', 'CARTE 11/07 SUPERMARCHE', '12,34', 'debit')],
        ancienSolde = '100,00 €',
        nouveauSolde = '87,66 €',
        debitTotal = '12,34'
    )

    transactions = FortuneoStatementParser(lines).parse()
    assert len(transactions) == 1
    assert transactions[0]['value'] == -12.34
    assert transactions[0]['date'] == '12/07/2026'
    assert transactions[0]['label'] == 'CARTE 11/07 SUPERMARCHE'

def testParseDebitAndCreditOnTheSameStatement():

    lines = buildStatement(
        [
            transactionLine('12/07', '12/07/2026', 'CARTE 11/07 SUPERMARCHE', '12,34', 'debit'),
            transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '1 000,00', 'credit')
        ],
        nouveauSolde = '987,66 €',
        debitTotal = '12,34',
        creditTotal = '1 000,00'
    )

    transactions = FortuneoStatementParser(lines).parse()
    assert [transaction['value'] for transaction in transactions] == [-12.34, 1000.0]

def testParseTransactionsOnASecondPage():

    lines = buildStatement(
        [transactionLine('12/07', '12/07/2026', 'CARTE 11/07 SUPERMARCHE', '12,34', 'debit')],
        secondPageTransactionLines = [
            transactionLine(
                '13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '1 000,00', 'credit',
                offset = SECOND_PAGE_OFFSET
            )
        ],
        nouveauSolde = '987,66 €',
        debitTotal = '12,34',
        creditTotal = '1 000,00'
    )

    transactions = FortuneoStatementParser(lines).parse()
    assert [transaction['value'] for transaction in transactions] == [-12.34, 1000.0]

def testSetColumnBoundariesFromHeaderLine():

    parser = FortuneoStatementParser([])

    # page 1 is the layout the boundaries were measured on, it shifts them by nothing
    parser.setColumnBoundariesFromHeaderLine(headerTableLine())
    assert parser.columnBoundaries == FortuneoStatementParser.COLUMN_BOUNDARIES

    parser.setColumnBoundariesFromHeaderLine(headerTableLine(offset = SECOND_PAGE_OFFSET))
    assert parser.columnBoundaries['date_valeur'] == {
        'x0': 82 + SECOND_PAGE_OFFSET,
        'x1': 132 + SECOND_PAGE_OFFSET
    }

def testValueDateOnASecondPageNeedsTheCalibratedBoundaries():

    parser = FortuneoStatementParser([])
    valueDate = word('20/07/2026', 89.28, 129.31, offset = SECOND_PAGE_OFFSET)

    # the page 1 window closes at 132, only 2.69 points past the end of a value date cell, so a
    # cell shifted by 4.56 ends at 133.87 and falls outside it
    assert parser.isDateValeurWord(valueDate) == False

    parser.setColumnBoundariesFromHeaderLine(headerTableLine(offset = SECOND_PAGE_OFFSET))
    assert parser.isDateValeurWord(valueDate) == True

def testMultiLineLabel():

    lines = buildStatement(
        [transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')],
        nouveauSolde = '50,00 €',
        creditTotal = '50,00'
    )
    # single cells sitting in the label column belong to the transaction above
    lines.insert(5, [word('VIR DE M MARTIN DUPONT', 135.84, 270.98)])
    lines.insert(6, [word('CH3W26201M000000', 135.84, 214.98)])

    transactions = FortuneoStatementParser(lines).parse()
    assert transactions[0]['label'] == 'VIR INST M MARTIN DUPONT VIR DE M MARTIN DUPONT CH3W26201M000000'

def testIsDateWord():

    parser = FortuneoStatementParser([])
    assert parser.isDateWord(word('20/07', 53.76, 73.78)) == True
    # a full date belongs to the date de valeur column, not the date one
    assert parser.isDateWord(word('20/07/2026', 89.28, 129.31)) == False
    assert parser.isDateWord(word('NOUVEAU SOLDE', 53.76, 132.27)) == False

def testIsDateValeurWord():

    parser = FortuneoStatementParser([])
    assert parser.isDateValeurWord(word('20/07/2026', 89.28, 129.31)) == True
    assert parser.isDateValeurWord(word('20/07', 53.76, 73.78)) == False
    # labels start at 135.84, they must not be read as a value date
    assert parser.isDateValeurWord(word('VIR INST M MARTIN DUPONT', 135.84, 278.09)) == False

def testIsDebitLine():

    parser = FortuneoStatementParser([])
    debit = transactionLine('12/07', '12/07/2026', 'CARTE 11/07 SUPERMARCHE', '12,34', 'debit')
    credit = transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')

    assert parser.isDebitLine(debit) == True
    assert parser.isDebitLine(credit) == False

def testIsCreditLine():

    parser = FortuneoStatementParser([])
    debit = transactionLine('12/07', '12/07/2026', 'CARTE 11/07 SUPERMARCHE', '12,34', 'debit')
    credit = transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')

    assert parser.isCreditLine(credit) == True
    assert parser.isCreditLine(debit) == False

def testNouveauSoldeLineIsNotATransaction():

    # 4 cells, and the amount sits inside the credit column: only the strict boundary test and
    # the date regex keep it out
    line = [
        word('NOUVEAU SOLDE', 53.76, 132.27),
        word('CRÉDITEUR', 135.36, 187.86),
        word('AU 31 JUILLET 2026', 190.56, 277.59),
        word('1 050,00 €', 511.2, 549.36)
    ]

    parser = FortuneoStatementParser([])
    assert parser.isCreditLine(line) == False
    assert parser.isDebitLine(line) == False

def testExtractAmount():

    parser = FortuneoStatementParser([])
    assert parser.extractAmount('50,00') == 50.0
    # fortuneo separates thousands with a space, not a dot
    assert parser.extractAmount('1 000,00') == 1000.0
    assert parser.extractAmount('1 050,00 €') == 1050.0
    assert parser.extractAmount('0,00 €') == 0.0

def testExtractIban():

    parser = FortuneoStatementParser([])
    assert parser.extractIban('IBAN FR76 3000 1000 0100 0000 0000 123 BIC FTNOFRP1XXX') == 'FR76 3000 1000 0100 0000 0000 123'
    assert parser.extractIban('NUMÉRO DE COMPTE') == None

def testGetTransactionYear():

    parser = FortuneoStatementParser([])
    parser.setStatementPeriodFromLine([word('Arrêté au 31 juillet 2026', 263.52, 386.41)])
    assert parser.getTransactionYear('20/07', '20/07/2026') == '2026'

    parser = FortuneoStatementParser([])
    parser.setStatementPeriodFromLine([word('Arrêté au 31 janvier 2026', 263.52, 386.41)])
    # a december operation listed on a january statement belongs to the previous year
    assert parser.getTransactionYear('31/12', '02/01/2026') == '2025'
    assert parser.getTransactionYear('05/01', '05/01/2026') == '2026'

def testGetTransactionYearFallsBackOnTheValueDate():

    # no 'Arrêté au' line was found
    parser = FortuneoStatementParser([])
    assert parser.getTransactionYear('20/07', '20/07/2026') == '2026'
    assert parser.getTransactionYear('31/12', '02/01/2027') == '2026'

def testDateIsPaddedWithALeadingZero():

    lines = buildStatement(
        [transactionLine('1/07', '01/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')],
        nouveauSolde = '50,00 €',
        creditTotal = '50,00'
    )

    transactions = FortuneoStatementParser(lines).parse()
    assert transactions[0]['date'] == '01/07/2026'

def testBalanceCheckRaisesOnAMisclassifiedAmount():

    # the statement says 1 000,00 was credited, but the amount cell sits in the debit column
    lines = buildStatement(
        [transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '1 000,00', 'debit')],
        nouveauSolde = '1 000,00 €',
        creditTotal = '1 000,00'
    )

    with pytest.raises(Exception) as error:
        FortuneoStatementParser(lines).parse()
    assert 'do not match the statement balance' in str(error.value)

def testBalanceCheckRaisesOnAMissedTransaction():

    lines = buildStatement(
        [transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')],
        nouveauSolde = '1 050,00 €',
        creditTotal = '1 050,00'
    )

    with pytest.raises(Exception):
        FortuneoStatementParser(lines).parse()

def testBalanceCheckToleratesFloatingPointError():

    # 0.1 summed twelve times is not exactly 1.2 in binary floating point
    lines = buildStatement(
        [transactionLine('0%d/07' % (index + 1), '0%d/07/2026' % (index + 1), 'VIR INST M MARTIN DUPONT', '0,10', 'credit') for index in range(9)]
        + [transactionLine('1%d/07' % index, '1%d/07/2026' % index, 'VIR INST M MARTIN DUPONT', '0,10', 'credit') for index in range(3)],
        nouveauSolde = '1,20 €',
        creditTotal = '1,20'
    )

    transactions = FortuneoStatementParser(lines).parse()
    assert len(transactions) == 12

def testBalanceCheckHandlesADebiteurBalance():

    lines = buildStatement(
        [transactionLine('12/07', '12/07/2026', 'CARTE 11/07 SUPERMARCHE', '50,00', 'debit')],
        nouveauSolde = '50,00 €',
        debitTotal = '50,00',
        soldeKeyword = 'DÉBITEUR'
    )

    transactions = FortuneoStatementParser(lines).parse()
    assert transactions[0]['value'] == -50.0

def testRaisesWhenTheBalanceRowsAreMissing():

    lines = buildStatement(
        [transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')],
        withBalanceRows = False
    )

    with pytest.raises(Exception) as error:
        FortuneoStatementParser(lines).parse()
    assert 'Could not find the ANCIEN SOLDE' in str(error.value)

def testRaisesWhenTheIbanIsMissing():

    lines = buildStatement(
        [transactionLine('13/07', '13/07/2026', 'VIR INST M MARTIN DUPONT', '50,00', 'credit')],
        nouveauSolde = '50,00 €',
        creditTotal = '50,00',
        withIban = False
    )

    with pytest.raises(Exception) as error:
        FortuneoStatementParser(lines).parse()
    assert 'Could not find the IBAN' in str(error.value)
