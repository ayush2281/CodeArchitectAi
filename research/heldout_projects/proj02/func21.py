def order_loada(x):
    return x * 2

def ticket_loadb(x):
    return x > 1

def task_auditc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return task_auditc(list(filter(ticket_loadb, items)), order_loada)
