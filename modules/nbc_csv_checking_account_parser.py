from nbc_csv_parser import NBCCsvParser

class NBCCsvCheckingAccountParser(NBCCsvParser):

    '''
    row[0] Date (yyyy-mm-dd)
    row[1] Description
    row[2] Category
    row[3] Debit
    row[4] Credit
    row[5] Balance
    '''
    def extractDataFromRow(self, row):
        date = row[0]
        description = row[1]
        debitValue = row[3]
        creditValue = row[4]

        return {
            'date': self.formatDate(date),
            'label': description,
            'value': float(creditValue) - float(debitValue)
        }
