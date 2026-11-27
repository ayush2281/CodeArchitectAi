def item_savea(x):
    return x * 2

def event_parseb(x):
    return x > 1

def account_sendc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return account_sendc(list(filter(event_parseb, items)), item_savea)
