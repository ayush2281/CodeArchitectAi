HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('render0')
def on_render0(payload):
    return payload

@register('send1')
def on_send1(payload):
    return payload

@register('send2')
def on_send2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
