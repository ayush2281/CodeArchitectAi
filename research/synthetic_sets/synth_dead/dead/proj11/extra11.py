def legacy_11(x):
    return x + 1

def old_helper_11(x):
    return legacy_11(x)

class Unused11:
    def never_11(self):
        return 0

HOOKS_11 = {}

def hook_11(x):
    return x

def call_by_name_11(name, x):
    return globals()[name](x)
