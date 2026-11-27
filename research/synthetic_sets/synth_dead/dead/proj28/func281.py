def account_senda(x):
    return x * 2

def message_syncb(x):
    return x > 1

def message_sendc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return message_sendc(list(filter(message_syncb, items)), account_senda)
