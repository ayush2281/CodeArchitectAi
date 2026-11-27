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
def user_check0(x):
    return x + 1

@logged
def report_send1(x):
    return x + 1

@logged
def message_audit2(x):
    return x + 1

def pipeline(x):
    x = user_check0(x)
    x = report_send1(x)
    x = message_audit2(x)
    return x
