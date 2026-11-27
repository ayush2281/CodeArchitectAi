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
def item_build0(x):
    return x + 1

@logged
def message_sync1(x):
    return x + 1

@logged
def invoice_save2(x):
    return x + 1

def pipeline(x):
    x = item_build0(x)
    x = message_sync1(x)
    x = invoice_save2(x)
    return x
