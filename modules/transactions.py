from functools import reduce

def compute_balance(transactions):

    def add_transaction_value(a, b):
        return round(a + b['value'], 2)

    return reduce(add_transaction_value, transactions, 0)
