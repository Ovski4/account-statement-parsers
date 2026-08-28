import sys
import json
import os
import pytest

sys.path.append('./modules')
from fortuneo_statement_parser import FortuneoStatementParser

sys.path.append('./tests/files')
from releve_fortuneo_1 import fortuneo_lines_1

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

'''
Helpers building synthetic statements. The sample statement holds credits only, so the debit
column x range and the balance self check can only be covered this way. The x coordinates are
the ones measured on the real statement, the y ones are irrelevant to this parser.
'''
def word(value, x0, x1, y0 = 500.0):
    return {'value': value, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y0 + 9.0}

def headerTableLine():
    return [
        word('Date', 56.88, 74.22),
        word('Date de Valeur', 83.76, 139.34),
        word('Opération', 236.16, 273.94),
        word('Débit', 407.28, 427.28),
        word('Crédit', 495.36, 518.47)
    ]

def transactionLine(date, dateValeur, label, amount, column):
    boundaries = {'debit': (447.6, 463.17), 'credit': (532.08, 552.1)}
    x0, x1 = boundaries[column]

    return [
        word(date, 53.76, 73.78),
        word(dateValeur, 89.28, 129.31),
        word(label, 135.84, 278.09),
        word(amount, x0, x1)
    ]

def buildStatement(
    transactionLines,
    ancienSolde = '0,00 €',
    nouveauSolde = '0,00 €',
    debitTotal = '0,00',
    creditTotal = '0,00',
    soldeKeyword = 'CRÉDITEUR',
    withIban = True,
    withBalanceRows = True
):
    lines = []

    if withIban:
        lines.append([word('IBAN FR76 3000 1000 0100 0000 0000 123 BIC FTNOFRP1XXX', 58.08, 303.75)])

    lines.append([word('Arrêté au 31 juillet 2026', 263.52, 386.41)])
    lines.append(headerTableLine())

    if withBalanceRows:
        lines.append([word('ANCIEN SOLDE', 53.76, 121.76), word(ancienSolde, 528.96, 549.36)])

    lines.extend(transactionLines)

    if withBalanceRows:
        lines.append([
            word('TOTAL DES OPÉRATIONS DU RELEVÉ', 51.12, 205.63),
            word(debitTotal, 447.6, 463.17),
            word(creditTotal, 521.28, 552.42)
        ])
        lines.append([
            word('NOUVEAU SOLDE', 53.76, 132.27),
            word(soldeKeyword, 135.36, 187.86),
            word('AU 31 JUILLET 2026', 190.56, 277.59),
            word(nouveauSolde, 511.2, 549.36)
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
