import sys
import os
import json
import uuid
from datetime import datetime
sys.path.append('modules')
from credit_mutuel_statement_parser import CreditMutuelStatementParser
from caisse_epargne_statement_parser import CaisseEpargneStatementParser
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
    else:
        raise Exception('Unknown parser with name' + parser_name)

    transactions = parser.parse()

    return transactions

def generate_response(request, parser_name):
    file_path = request.args[b'statement'][0] 
    transactions = parse(file_path, 'credit-mutuel')

    return json.dumps(transactions, indent=2, ensure_ascii=False)

@route('/credit-mutuel/')
def statement(request):
    return generate_response(request, 'credit-mutuel')

@route('/caisse-epargne/')
def statement(request):
    return generate_response(request, 'caisse-epargne')

run('0.0.0.0', 80)
