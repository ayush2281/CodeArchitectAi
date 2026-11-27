HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('check0')
def on_check0(payload):
    return payload

@register('merge1')
def on_merge1(payload):
    return payload

@register('build2')
def on_build2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
