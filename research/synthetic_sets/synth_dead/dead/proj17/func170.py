def cart_checka(x):
    return x * 2

def message_checkb(x):
    return x > 1

def ticket_loadc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return ticket_loadc(list(filter(message_checkb, items)), cart_checka)
