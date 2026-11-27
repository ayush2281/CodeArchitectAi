HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('format0')
def on_format0(payload):
    return payload

@register('audit1')
def on_audit1(payload):
    return payload

@register('send2')
def on_send2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
