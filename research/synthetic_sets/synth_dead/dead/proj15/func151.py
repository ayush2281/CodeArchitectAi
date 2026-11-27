def ticket_synca(x):
    return x * 2

def report_syncb(x):
    return x > 1

def message_loadc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return message_loadc(list(filter(report_syncb, items)), ticket_synca)
