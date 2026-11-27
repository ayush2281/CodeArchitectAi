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
def event_render0(x):
    return x + 1

@logged
def order_update1(x):
    return x + 1

@logged
def user_render2(x):
    return x + 1

def pipeline(x):
    x = event_render0(x)
    x = order_update1(x)
    x = user_render2(x)
    return x
