import sys
import json
import argparse
sys.path.append('./modules')
from parser_factory import create_parser, parserConfigs
from transactions import compute_balance

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2

EPILOG = """\
examples:
  parse.py nbc-credit tests/files/nbc-credit-account.csv
  parse.py nbc-credit tests/files/nbc-credit-account.csv --balance
  parse.py --list

Every module appends './modules' to sys.path, so this script only works when run
from the repository root.

pdfminer lives in the image rather than on the host, so run it through compose:

  docker compose run --rm tests python parse.py nbc-credit tests/files/nbc-credit-account.csv

'docker compose run' does not publish ports unless you pass --service-ports, so the
tests service will not collide with an api container already holding port 80.

exit codes:
  0  success, JSON on stdout
  1  the parse failed, message on stderr
  2  bad usage, including an unknown parser name
"""

def build_argument_parser():
    argumentParser = argparse.ArgumentParser(
        prog='parse.py',
        description='Parse a bank statement and print the transactions as JSON.',
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    argumentParser.add_argument(
        'parser_name',
        nargs='?',
        help='which bank statement format to parse; see --list'
    )
    argumentParser.add_argument(
        'file_path',
        nargs='?',
        help='the statement to parse'
    )
    argumentParser.add_argument(
        '--balance',
        action='store_true',
        help='print the total of the transactions instead of the transactions'
    )
    argumentParser.add_argument(
        '--list',
        action='store_true',
        dest='list_parsers',
        help='print the available parser names and exit'
    )

    return argumentParser

def parse_statement(file_path, parser_name, balance):
    transactions = create_parser(file_path, parser_name).parse()

    if balance:
        return {'total': compute_balance(transactions)}

    return transactions

def main(argv=None):
    argumentParser = build_argument_parser()
    arguments = argumentParser.parse_args(argv)

    if arguments.list_parsers:
        print('\n'.join(parserConfigs))
        return EXIT_OK

    if arguments.parser_name is None or arguments.file_path is None:
        argumentParser.print_usage(sys.stderr)
        print('parse.py: error: a parser name and a file are required', file=sys.stderr)
        return EXIT_USAGE

    if arguments.parser_name not in parserConfigs:
        print('Unknown parser with name ' + arguments.parser_name, file=sys.stderr)
        print('Available parsers: ' + ', '.join(parserConfigs), file=sys.stderr)
        return EXIT_USAGE

    try:
        result = parse_statement(arguments.file_path, arguments.parser_name, arguments.balance)
    except Exception as error:
        print(error, file=sys.stderr)
        return EXIT_FAILURE

    print(json.dumps(result, indent=2, ensure_ascii=False))

    return EXIT_OK

if __name__ == '__main__':
    sys.exit(main())
