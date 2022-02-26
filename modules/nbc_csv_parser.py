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
                elif self.fileType != self.getFileType():
                    raise Exception("The given file does not contain expected data for this parser")
                else:
                    transactions.append(self.extractDataFromRow(row))

        return transactions

    def getFileType(self):
        raise NotImplementedError("Please Implement getFileType")

    def extractDataFromRow(self, row):
        raise NotImplementedError("Please Implement extractDataFromRow")

    def formatDate(self, value):
        dateRegex = r'(\d{4})-(\d{2})-(\d{2})'
        results = re.search(dateRegex, value)

        return results.group(3) + '/' + results.group(2) + '/' + results.group(1)

    '''
    Checking account header: Date;Description;Category;Debit;Credit;Balance
    Credit account header: Date;"card Number";Description;Category;Debit;Credit
    '''
    def guessFileTypeFromHeader(self, headerRow):
        return 'checking' if headerRow[1] == 'Description' else 'credit'
