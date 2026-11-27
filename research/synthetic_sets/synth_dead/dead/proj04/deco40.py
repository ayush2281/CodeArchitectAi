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
def order_load0(x):
    return x + 1

@logged
def ticket_load1(x):
    return x + 1

@logged
def task_audit2(x):
    return x + 1

def pipeline(x):
    x = order_load0(x)
    x = ticket_load1(x)
    x = task_audit2(x)
    return x
