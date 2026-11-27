def order_loada(x):
    return x * 2

def message_renderb(x):
    return x > 1

def task_parsec(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return task_parsec(list(filter(message_renderb, items)), order_loada)
