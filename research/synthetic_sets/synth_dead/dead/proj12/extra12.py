def legacy_12(x):
    return x + 1

def old_helper_12(x):
    return legacy_12(x)

class Unused12:
    def never_12(self):
        return 0

HOOKS_12 = {}

def hook_12(x):
    return x

def call_by_name_12(name, x):
    return globals()[name](x)
