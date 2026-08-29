import sys
sys.path.append('./modules')
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

def create_parser(file_path, parser_name):
    if parser_name not in parserConfigs:
        raise Exception('Unknown parser with name ' + parser_name)

    parserConfig = parserConfigs[parser_name]

    if parserConfig['type'] == 'pdf':
        pdfFile = open(file_path, 'rb')
        lines = PdfParser().parse(pdfFile)
        pdfFile.close()
        return parserConfig['module'](lines)

    return parserConfig['module'](file_path)

def parse(file_path, parser_name):
    return create_parser(file_path, parser_name).parse()
