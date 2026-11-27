def message_savea(x):
    return x * 2

def job_syncb(x):
    return x > 1

def cart_sendc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return cart_sendc(list(filter(job_syncb, items)), message_savea)
