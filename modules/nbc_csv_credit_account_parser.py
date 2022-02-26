from nbc_csv_parser import NBCCsvParser

class NBCCsvCreditAccountParser(NBCCsvParser):

    '''
    row[0] Date (yyyy-mm-dd)
    row[1] card Number
    row[2] Description
    row[3] Category
    row[4] Debit
    row[5] Credit
    '''
    def extractDataFromRow(self, row):
        date = row[0]
        description = row[2]
        debitValue = row[4]
        creditValue = row[5]

        return {
            'date': self.formatDate(date),
            'label': description,
            'value': float(creditValue) - float(debitValue)
        }
