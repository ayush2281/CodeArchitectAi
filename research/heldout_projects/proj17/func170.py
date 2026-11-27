def user_builda(x):
    return x * 2

def report_buildb(x):
    return x > 1

def item_auditc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return item_auditc(list(filter(report_buildb, items)), user_builda)
