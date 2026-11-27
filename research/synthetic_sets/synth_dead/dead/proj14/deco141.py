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
def item_build0(x):
    return x + 1

@logged
def event_parse1(x):
    return x + 1

@logged
def item_send2(x):
    return x + 1

def pipeline(x):
    x = item_build0(x)
    x = event_parse1(x)
    x = item_send2(x)
    return x
