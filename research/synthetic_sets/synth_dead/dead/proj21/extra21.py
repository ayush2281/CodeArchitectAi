def legacy_21(x):
    return x + 1

def old_helper_21(x):
    return legacy_21(x)

class Unused21:
    def never_21(self):
        return 0

HOOKS_21 = {}

def hook_21(x):
    return x

def call_by_name_21(name, x):
    return globals()[name](x)
