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
def message_save0(x):
    return x + 1

@logged
def job_sync1(x):
    return x + 1

@logged
def cart_send2(x):
    return x + 1

def pipeline(x):
    x = message_save0(x)
    x = job_sync1(x)
    x = cart_send2(x)
    return x
