import json
import pytest

from nbc_csv_chequing_or_savings_account_parser import NBCCsvChequingOrSavingsAccountParser

def testParse():

    nbcParser = NBCCsvChequingOrSavingsAccountParser('./tests/files/nbc-chequing-account.csv')
    transactions = nbcParser.parse()
    with open('./tests/files/expected-results-nbc-chequing-account.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData
