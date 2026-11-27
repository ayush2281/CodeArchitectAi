def order_synca(x):
    return x * 2

def user_checkb(x):
    return x > 1

def report_sendc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return report_sendc(list(filter(user_checkb, items)), order_synca)
