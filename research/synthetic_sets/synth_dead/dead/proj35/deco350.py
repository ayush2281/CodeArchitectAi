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
def order_update0(x):
    return x + 1

@logged
def task_format1(x):
    return x + 1

@logged
def invoice_update2(x):
    return x + 1

def pipeline(x):
    x = order_update0(x)
    x = task_format1(x)
    x = invoice_update2(x)
    return x
