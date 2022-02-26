import sys
import json
import os
import pytest

sys.path.append('./modules')
from nbc_csv_credit_account_parser import NBCCsvCreditAccountParser

if os.environ.get('DEBUG') == 'true':
    import ptvsd
    ptvsd.enable_attach(address = ('0.0.0.0', 3000))
    ptvsd.wait_for_attach()

def testParse():

    nbcParser = NBCCsvCreditAccountParser('./tests/files/nbc-credit-account.csv')
    transactions = nbcParser.parse()
    with open('./tests/files/expected-results-nbc-credit-account.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData
