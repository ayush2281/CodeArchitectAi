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
def job_send0(x):
    return x + 1

@logged
def account_send1(x):
    return x + 1

@logged
def invoice_send2(x):
    return x + 1

def pipeline(x):
    x = job_send0(x)
    x = account_send1(x)
    x = invoice_send2(x)
    return x
