def message_parsea(x):
    return x * 2

def item_buildb(x):
    return x > 1

def event_auditc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return event_auditc(list(filter(item_buildb, items)), message_parsea)
