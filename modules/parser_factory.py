import sys
sys.path.append('./modules')
from functools import reduce
from credit_mutuel_statement_parser import CreditMutuelStatementParser
from caisse_epargne_statement_parser import CaisseEpargneStatementParser
from n26_statement_parser import N26StatementParser
from boursorama_statement_parser import BoursoramaStatementParser
from nbc_csv_chequing_or_savings_account_parser import NBCCsvChequingOrSavingsAccountParser
from nbc_csv_credit_account_parser import NBCCsvCreditAccountParser
from pdf_parser import PdfParser

parserConfigs = {
    'nbc-credit': {
        'module': NBCCsvCreditAccountParser,
        'type': 'csv'
    },
    'nbc-chequing-or-savings': {
        'module': NBCCsvChequingOrSavingsAccountParser,
        'type': 'csv'
    },
    'credit-mutuel': {
        'module': CreditMutuelStatementParser,
        'type': 'pdf'
    },
    'caisse-epargne': {
        'module': CaisseEpargneStatementParser,
        'type': 'pdf'
    },
    'n26': {
        'module': N26StatementParser,
        'type': 'pdf'
    },
    'boursorama': {
        'module': BoursoramaStatementParser,
        'type': 'pdf'
    }
}

def parse(file_path, parser_name):
    if parser_name not in parserConfigs:
        raise Exception('Unknown parser with name ' + parser_name)

    parserConfig = parserConfigs[parser_name]

    if parserConfig['type'] == 'pdf':
        pdfFile = open(file_path, 'rb')
        lines = PdfParser().parse(pdfFile)
        pdfFile.close()
        parser = parserConfig['module'](lines)
    else:
        parser = parserConfig['module'](file_path)

    transactions = parser.parse()

    return transactions

def compute_balance(transactions):

    def add_transaction_value(a, b):
        return round(a + b['value'], 2)

    return reduce(add_transaction_value, transactions, 0)
