HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('check0')
def on_check0(payload):
    return payload

@register('load1')
def on_load1(payload):
    return payload

@register('send2')
def on_send2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
