def legacy_23(x):
    return x + 1

def old_helper_23(x):
    return legacy_23(x)

class Unused23:
    def never_23(self):
        return 0

HOOKS_23 = {}

def hook_23(x):
    return x

def call_by_name_23(name, x):
    return globals()[name](x)
