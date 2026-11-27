def ticket_rendera(x):
    return x * 2

def cart_formatb(x):
    return x > 1

def user_auditc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return user_auditc(list(filter(cart_formatb, items)), ticket_rendera)
