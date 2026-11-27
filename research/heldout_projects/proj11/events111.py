HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('send0')
def on_send0(payload):
    return payload

@register('check1')
def on_check1(payload):
    return payload

@register('sync2')
def on_sync2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
