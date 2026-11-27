HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('send0')
def on_send0(payload):
    return payload

@register('format1')
def on_format1(payload):
    return payload

@register('build2')
def on_build2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
