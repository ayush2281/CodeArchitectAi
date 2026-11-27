def order_checka(x):
    return x * 2

def cart_updateb(x):
    return x > 1

def account_buildc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return account_buildc(list(filter(cart_updateb, items)), order_checka)
