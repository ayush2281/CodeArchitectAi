def legacy_5(x):
    return x + 1

def old_helper_5(x):
    return legacy_5(x)

class Unused5:
    def never_5(self):
        return 0

HOOKS_5 = {}

def hook_5(x):
    return x

def call_by_name_5(name, x):
    return globals()[name](x)
