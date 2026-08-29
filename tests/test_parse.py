import sys
import json
import subprocess

def runParseScript(*arguments):

    return subprocess.run(
        [sys.executable, 'parse.py'] + list(arguments),
        capture_output=True,
        text=True
    )

def testParsePrintsTheTransactionsAsJson():

    result = runParseScript('nbc-credit', './tests/files/nbc-credit-account.csv')
    with open('./tests/files/expected-results-nbc-credit-account.json') as file:
        expectedData = json.loads(file.read())

    assert result.returncode == 0
    assert json.loads(result.stdout) == expectedData

def testParseBalancePrintsTheTotal():

    result = runParseScript('nbc-credit', './tests/files/nbc-credit-account.csv', '--balance')

    assert result.returncode == 0
    assert json.loads(result.stdout) == {'total': -49.17}

def testParseListPrintsTheParserNames():

    result = runParseScript('--list')

    assert result.returncode == 0
    assert 'nbc-credit' in result.stdout.split('\n')
    assert 'boursorama' in result.stdout.split('\n')

def testParseUnknownParserNameExitsTwo():

    result = runParseScript('does-not-exist', './tests/files/nbc-credit-account.csv')

    assert result.returncode == 2
    assert result.stdout == ''
    assert 'does-not-exist' in result.stderr
    assert 'nbc-credit' in result.stderr

def testParseMissingFileExitsOne():

    result = runParseScript('nbc-credit', './tests/files/does-not-exist.csv')

    assert result.returncode == 1
    assert result.stdout == ''
    assert 'does-not-exist.csv' in result.stderr

def testParseWithoutArgumentsExitsTwo():

    result = runParseScript()

    assert result.returncode == 2
    assert result.stdout == ''
    assert 'usage:' in result.stderr
