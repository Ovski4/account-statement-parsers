import json
import pytest

import parser_factory
from parser_factory import create_parser, parserConfigs
from nbc_csv_credit_account_parser import NBCCsvCreditAccountParser

def testCreateParserCsv():

    parser = create_parser('./tests/files/nbc-credit-account.csv', 'nbc-credit')
    transactions = parser.parse()
    with open('./tests/files/expected-results-nbc-credit-account.json') as file:
        expectedData = json.loads(file.read())
    assert transactions == expectedData

def testCreateParserPdfFeedsParsedLinesToTheParser(monkeypatch):

    class StubParser:
        def __init__(self, lines):
            self.lines = lines
        def parse(self):
            return self.lines

    # Create a parser config for the test PDF file
    monkeypatch.setitem(
        parser_factory.parserConfigs,
        'pdf-under-test',
        {'module': StubParser, 'type': 'pdf'}
    )

    parser = create_parser('./tests/files/test.pdf', 'pdf-under-test')

    assert parser.lines[0][0]['value'] == 'Text here'

def testCreateParserPdfAppliesTheConfiguredCellFilter(monkeypatch):

    class StubParser:
        def __init__(self, lines):
            self.lines = lines

    monkeypatch.setitem(
        parser_factory.parserConfigs,
        'pdf-under-test',
        {'module': StubParser, 'type': 'pdf', 'keepCell': lambda cell: cell[5] != 'Text here'}
    )

    parser = create_parser('./tests/files/test.pdf', 'pdf-under-test')

    assert 'Text here' not in [word['value'] for line in parser.lines for word in line]

def testCreateParserReturnsTheConfiguredParser():

    parser = create_parser('./tests/files/nbc-credit-account.csv', 'nbc-credit')

    assert isinstance(parser, NBCCsvCreditAccountParser)

def testCreateParserUnknownParserName():

    with pytest.raises(Exception):
        create_parser('./tests/files/nbc-credit-account.csv', 'does-not-exist')

def testEveryParserConfigIsUsable():

    for name, config in parserConfigs.items():
        assert config['type'] in ('pdf', 'csv')
        assert callable(config['module'])
        assert 'keepCell' not in config or callable(config['keepCell'])
