HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('update0')
def on_update0(payload):
    return payload

@register('format1')
def on_format1(payload):
    return payload

@register('parse2')
def on_parse2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
