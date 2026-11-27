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
def task_format0(x):
    return x + 1

@logged
def job_sync1(x):
    return x + 1

@logged
def account_parse2(x):
    return x + 1

def pipeline(x):
    x = task_format0(x)
    x = job_sync1(x)
    x = account_parse2(x)
    return x
