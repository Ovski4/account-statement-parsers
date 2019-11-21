import sys
import os
import json
import mysql.connector
import uuid
from datetime import datetime

sys.path.append('modules')

from ccmparser import CCMParser
from pdfparser import PdfParser

ccm_folder = '/usr/src/app/ccm_folder'

def extract_transactions(file_path, file_name):
    pdfFile = open(file_path, 'rb')
    lines = PdfParser().parse(pdfFile)
    pdfFile.close()
    ccmparser = CCMParser(lines)
    transactions = ccmparser.parse()

    return transactions

def save_in_file(transactions, file_name):
    file_name_without_extension = file_name[:-4]
    json_file_path = '/usr/src/app/parsed_files/' + file_name_without_extension + '.json'

    print('creating ' + json_file_path)
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(transactions, json_file, ensure_ascii=False)

def save_in_mysql(transactions):
    mydb = mysql.connector.connect(
        host="mysql",
        user="expenses_categorizer",
        passwd="expenses_categorizer",
        database="expenses_categorizer"
    )

    mycursor = mydb.cursor()

    for transaction in transactions:
        date_time = datetime.strptime(transaction.get('date'), "%d/%m/%Y")
        date_time_string = date_time.strftime("%Y-%m-%d 00:00:00")
        sql = "INSERT INTO transaction (id, label, amount, created_at, account) VALUES (%s, %s, %s, %s, %s)"
        val = (
            str(uuid.uuid1()),
            transaction.get('label'),
            transaction.get('value'),
            date_time_string,
            transaction.get('account')
        )
        mycursor.execute(sql, val)
        mydb.commit()

for dirpath, dirnames, files in os.walk('/usr/src/app/ccm_folder'):
    for file_name in files:
        if file_name.endswith('.pdf') and file_name.startswith('releve'):
            file_path = os.path.join(dirpath, file_name)
            print('parsing ' + file_path,)
            transactions = extract_transactions(file_path, file_name)
            #save_in_file(transactions, file_name)
            save_in_mysql(transactions)
