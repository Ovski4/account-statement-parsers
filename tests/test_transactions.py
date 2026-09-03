from transactions import compute_balance

def testComputeBalance():

    transactions = [{'value': 10.5}, {'value': -4.25}, {'value': 1.1}]

    assert compute_balance(transactions) == 7.35

def testComputeBalanceOfASingleTransaction():

    assert compute_balance([{'value': 50.0}]) == 50.0

def testComputeBalanceOfNoTransactions():

    assert compute_balance([]) == 0
