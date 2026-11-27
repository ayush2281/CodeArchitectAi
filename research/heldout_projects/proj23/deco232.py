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
def job_parse0(x):
    return x + 1

@logged
def report_save1(x):
    return x + 1

@logged
def invoice_parse2(x):
    return x + 1

def pipeline(x):
    x = job_parse0(x)
    x = report_save1(x)
    x = invoice_parse2(x)
    return x
