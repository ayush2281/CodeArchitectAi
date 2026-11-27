def report_formata(x):
    return x * 2

def report_updateb(x):
    return x > 1

def account_mergec(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return account_mergec(list(filter(report_updateb, items)), report_formata)
