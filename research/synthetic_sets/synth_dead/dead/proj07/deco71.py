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
def order_format0(x):
    return x + 1

@logged
def item_sync1(x):
    return x + 1

@logged
def item_check2(x):
    return x + 1

def pipeline(x):
    x = order_format0(x)
    x = item_sync1(x)
    x = item_check2(x)
    return x
