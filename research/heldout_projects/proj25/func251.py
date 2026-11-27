def user_mergea(x):
    return x * 2

def account_loadb(x):
    return x > 1

def order_updatec(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return order_updatec(list(filter(account_loadb, items)), user_mergea)
