HANDLERS = {}

def register(name):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco

@register('render0')
def on_render0(payload):
    return payload

@register('audit1')
def on_audit1(payload):
    return payload

@register('check2')
def on_check2(payload):
    return payload

def dispatch(name, payload):
    return HANDLERS[name](payload)
