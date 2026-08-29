import sys
import json
import pytest

sys.path.append('./modules')
import parser_factory
from parser_factory import parse, compute_balance, parserConfigs

def testParseCsv():

    transactions = parse('./tests/files/nbc-credit-account.csv', 'nbc-credit')
    with open('./tests/files/expected-results-nbc-credit-account.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

def testParsePdfFeedsParsedLinesToTheParser(monkeypatch):

    class LineCollector:
        def __init__(self, lines):
            self.lines = lines
        def parse(self):
            return self.lines

    monkeypatch.setitem(
        parser_factory.parserConfigs,
        'pdf-under-test',
        {'module': LineCollector, 'type': 'pdf'}
    )

    lines = parse('./tests/files/test.pdf', 'pdf-under-test')

    assert lines[0][0]['value'] == 'Text here'

def testParseUnknownParserName():

    with pytest.raises(Exception):
        parse('./tests/files/nbc-credit-account.csv', 'does-not-exist')

def testEveryParserConfigIsUsable():

    for name, config in parserConfigs.items():
        assert config['type'] in ('pdf', 'csv')
        assert callable(config['module'])

def testComputeBalance():

    transactions = [{'value': 10.5}, {'value': -4.25}, {'value': 1.1}]

    assert compute_balance(transactions) == 7.35

def testComputeBalanceOfASingleTransaction():

    assert compute_balance([{'value': 50.0}]) == 50.0

def testComputeBalanceOfNoTransactions():

    assert compute_balance([]) == 0
