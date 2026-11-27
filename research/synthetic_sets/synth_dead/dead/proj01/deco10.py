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
def invoice_format0(x):
    return x + 1

@logged
def user_format1(x):
    return x + 1

@logged
def event_send2(x):
    return x + 1

def pipeline(x):
    x = invoice_format0(x)
    x = user_format1(x)
    x = event_send2(x)
    return x
