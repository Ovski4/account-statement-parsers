import re
import csv

class NBCCsvParser:

    def __init__(self, csvFile):
        self.csvFile = csvFile
        self.fileType = None

    def parse(self):
        transactions = []

        with open(self.csvFile, newline='') as csvfile:
            csvReader = csv.reader(csvfile, delimiter=';')

            for row in csvReader:
                if self.fileType is None:
                    self.fileType = self.guessFileTypeFromHeader(row)
                elif self.fileType == 'checking':
                    transactions.append(self.extractDataFromCheckingAccountRow(row))

        return transactions

    '''
    row[0] Date (yyyy-mm-dd)
    row[1] Description
    row[2] Category
    row[3] Debit
    row[4] Credit
    row[5] Balance
    '''
    def extractDataFromCheckingAccountRow(self, row):
        date = row[0]
        description = row[1]
        debitValue = row[3]
        creditValue = row[4]

        return {
            'date': self.formatDate(date),
            'label': description,
            'value': float(creditValue) - float(debitValue)
        }

    def formatDate(self, value):
        dateRegex = r'(\d{4})-(\d{2})-(\d{2})'
        results = re.search(dateRegex, value)

        return results.group(3) + '/' + results.group(2) + '/' + results.group(1)
    
    def guessFileTypeFromHeader(self, headerRow):
        return 'checking'