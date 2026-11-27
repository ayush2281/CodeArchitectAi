HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('sync0')
def on_sync0(payload):
    return payload

@register('merge1')
def on_merge1(payload):
    return payload

@register('send2')
def on_send2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
