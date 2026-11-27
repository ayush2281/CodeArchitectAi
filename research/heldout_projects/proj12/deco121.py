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
def order_update0(x):
    return x + 1

@logged
def user_render1(x):
    return x + 1

@logged
def user_load2(x):
    return x + 1

def pipeline(x):
    x = order_update0(x)
    x = user_render1(x)
    x = user_load2(x)
    return x
