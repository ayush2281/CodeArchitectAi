import functools

def logged(fn):
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        note(fn.__name__)
        return fn(*a, **kw)
    return wrapper

def note(name):
    return name

@logged
def order_send0(x):
    return x + 1

@logged
def report_parse1(x):
    return x + 1

@logged
def task_load2(x):
    return x + 1

def pipeline(x):
    x = order_send0(x)
    x = report_parse1(x)
    x = task_load2(x)
    return x
