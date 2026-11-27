def order_senda(x):
    return x * 2

def task_renderb(x):
    return x > 1

def report_updatec(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return report_updatec(list(filter(task_renderb, items)), order_senda)
