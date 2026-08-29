import sys
import json
sys.path.append('modules')
from parser_factory import create_parser
from transactions import compute_balance
from klein import run, route

def dump_transactions(request, parser_name):
    file_path = request.args[b'statement'][0]
    transactions = create_parser(file_path, parser_name).parse()

    return json.dumps(transactions, indent=2, ensure_ascii=False)

def dump_balance(request, parser_name):
    file_path = request.args[b'statement'][0]
    transactions = create_parser(file_path, parser_name).parse()

    return json.dumps({'total': compute_balance(transactions)}, indent=2, ensure_ascii=False)

@route('/<parser_name>')
def statement(request, parser_name):
    return dump_transactions(request, parser_name)

@route('/<parser_name>/balance')
def balance(request, parser_name):
    return dump_balance(request, parser_name)

run('0.0.0.0', 80)
