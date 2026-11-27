HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('audit0')
def on_audit0(payload):
    return payload

@register('audit1')
def on_audit1(payload):
    return payload

@register('load2')
def on_load2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
