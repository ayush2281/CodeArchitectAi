HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('update0')
def on_update0(payload):
    return payload

@register('sync1')
def on_sync1(payload):
    return payload

@register('merge2')
def on_merge2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
