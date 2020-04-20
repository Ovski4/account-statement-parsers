import sys
import os
import json
import uuid
from datetime import datetime
sys.path.append('modules')
from ccmparser import CCMParser
from pdfparser import PdfParser
from klein import run, route

def parse(file_path):
    pdfFile = open(file_path, 'rb')
    lines = PdfParser().parse(pdfFile)
    pdfFile.close()
    ccmparser = CCMParser(lines)
    transactions = ccmparser.parse()

    return transactions

@route('/')
def statement(request):
    file_path = request.args[b'statement'][0] 
    transactions = parse(file_path)

    return json.dumps(transactions, indent=2, ensure_ascii=False)

run('0.0.0.0', 80)
