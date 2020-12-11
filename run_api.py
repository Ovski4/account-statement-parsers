import sys
import os
import json
import uuid
from datetime import datetime
sys.path.append('modules')
from credit_mutuel_statement_parser import CreditMutuelStatementParser
from caisse_epargne_statement_parser import CaisseEpargneStatementParser
from functools import reduce
from n26_statement_parser import N26StatementParser
from boursorama_statement_parser import BoursoramaStatementParser
from pdf_parser import PdfParser
from klein import run, route

def parse(file_path, parser_name):
    pdfFile = open(file_path, 'rb')
    lines = PdfParser().parse(pdfFile)
    pdfFile.close()
    if (parser_name == 'credit-mutuel'):
        parser = CreditMutuelStatementParser(lines)
    elif (parser_name == 'caisse-epargne'):
        parser = CaisseEpargneStatementParser(lines)
    elif (parser_name == 'n26'):
        parser = N26StatementParser(lines)
    elif (parser_name == 'boursorama'):
        parser = BoursoramaStatementParser(lines)
    else:
        raise Exception('Unknown parser with name' + parser_name)

    transactions = parser.parse()

    return transactions

def dump_transactions(request, parser_name):
    file_path = request.args[b'statement'][0]
    transactions = parse(file_path, parser_name)

    return json.dumps(transactions, indent=2, ensure_ascii=False)

def dump_balance(request, parser_name):

    def add_transaction_value(a, b):
        if isinstance(a ,dict):
            a = a['value']
        return round(a + b['value'], 2)

    file_path = request.args[b'statement'][0]
    transactions = parse(file_path, parser_name)
    total = reduce(add_transaction_value, transactions)

    return json.dumps({'total': total}, indent=2, ensure_ascii=False)

@route('/<parser_name>')
def statement(request, parser_name):
    return dump_transactions(request, parser_name)

@route('/<parser_name>/balance')
def balance(request, parser_name):
    return dump_balance(request, parser_name)

run('0.0.0.0', 80)
