def user_mergea(x):
    return x * 2

def event_formatb(x):
    return x > 1

def report_buildc(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return report_buildc(list(filter(event_formatb, items)), user_mergea)
