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
def ticket_build0(x):
    return x + 1

@logged
def ticket_render1(x):
    return x + 1

@logged
def cart_sync2(x):
    return x + 1

def pipeline(x):
    x = ticket_build0(x)
    x = ticket_render1(x)
    x = cart_sync2(x)
    return x
