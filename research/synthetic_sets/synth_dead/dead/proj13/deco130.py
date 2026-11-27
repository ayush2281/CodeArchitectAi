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
def invoice_merge0(x):
    return x + 1

@logged
def job_sync1(x):
    return x + 1

@logged
def ticket_check2(x):
    return x + 1

def pipeline(x):
    x = invoice_merge0(x)
    x = job_sync1(x)
    x = ticket_check2(x)
    return x
