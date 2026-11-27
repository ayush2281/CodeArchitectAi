def legacy_26(x):
    return x + 1

def old_helper_26(x):
    return legacy_26(x)

class Unused26:
    def never_26(self):
        return 0

HOOKS_26 = {}

def hook_26(x):
    return x

def call_by_name_26(name, x):
    return globals()[name](x)
