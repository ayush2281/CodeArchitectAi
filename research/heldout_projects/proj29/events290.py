HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('build0')
def on_build0(payload):
    return payload

@register('format1')
def on_format1(payload):
    return payload

@register('audit2')
def on_audit2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
