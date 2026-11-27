HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('parse0')
def on_parse0(payload):
    return payload

@register('sync1')
def on_sync1(payload):
    return payload

@register('update2')
def on_update2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
