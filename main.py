import sys
import os
import json
sys.path.append('modules')

from ccmparser import CCMParser
from pdfparser import PdfParser

ccm_folder = '/usr/src/app/ccm_folder'

def parse_and_dump(file_path, file_name):
    pdfFile = open(file_path, 'rb')
    lines = PdfParser().parse(pdfFile)
    pdfFile.close()
    ccmparser = CCMParser(lines)
    transactions = ccmparser.parse()

    file_name_without_extension = file_name[:-4]
    json_file_path = '/usr/src/app/parsed_files/' + file_name_without_extension + '.json'

    print('creating ' + json_file_path)
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(transactions, json_file, ensure_ascii=False)

for dirpath, dirnames, files in os.walk('/usr/src/app/ccm_folder'):
    for file_name in files:
        if file_name.endswith('.pdf') and file_name.startswith('releve'):
            file_path = os.path.join(dirpath, file_name)
            print('parsing ' + file_path,)
            parse_and_dump(file_path, file_name)
