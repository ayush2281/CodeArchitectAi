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
def cart_parse0(x):
    return x + 1

@logged
def user_merge1(x):
    return x + 1

@logged
def account_load2(x):
    return x + 1

def pipeline(x):
    x = cart_parse0(x)
    x = user_merge1(x)
    x = account_load2(x)
    return x
