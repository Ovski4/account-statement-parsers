import sys
import json
import pytest

sys.path.append('./modules')
import parser_factory
from parser_factory import create_parser, parse, parserConfigs
from nbc_csv_credit_account_parser import NBCCsvCreditAccountParser

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

    parser = create_parser('./tests/files/test.pdf', 'pdf-under-test')

    assert parser.lines[0][0]['value'] == 'Text here'
    assert parse('./tests/files/test.pdf', 'pdf-under-test') == parser.lines

def testCreateParserReturnsTheConfiguredParser():

    parser = create_parser('./tests/files/nbc-credit-account.csv', 'nbc-credit')

    assert isinstance(parser, NBCCsvCreditAccountParser)

def testCreateParserUnknownParserName():

    with pytest.raises(Exception):
        create_parser('./tests/files/nbc-credit-account.csv', 'does-not-exist')

def testParseUnknownParserName():

    with pytest.raises(Exception):
        parse('./tests/files/nbc-credit-account.csv', 'does-not-exist')

def testEveryParserConfigIsUsable():

    for name, config in parserConfigs.items():
        assert config['type'] in ('pdf', 'csv')
        assert callable(config['module'])
