import json
import pytest

from nbc_csv_credit_account_parser import NBCCsvCreditAccountParser

def testParse():

    nbcParser = NBCCsvCreditAccountParser('./tests/files/nbc-credit-account.csv')
    transactions = nbcParser.parse()
    with open('./tests/files/expected-results-nbc-credit-account.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData
