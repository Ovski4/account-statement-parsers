import re
import csv

class NBCCsvParser:

    def __init__(self, csvFile):
        self.csvFile = csvFile

    def parse(self):
        transactions = []

        with open(self.csvFile, newline='') as csvfile:
            csvReader = csv.reader(csvfile, delimiter=';')

            # skip the headers
            next(csvReader, None)

            for row in csvReader:
                transactions.append(self.extractDataFromRow(row))

        return transactions

    def extractDataFromRow(self, row):
        raise NotImplementedError("Please Implement extractDataFromRow")

    def formatDate(self, value):
        dateRegex = r'(\d{4})-(\d{2})-(\d{2})'
        results = re.search(dateRegex, value)

        return results.group(3) + '/' + results.group(2) + '/' + results.group(1)
