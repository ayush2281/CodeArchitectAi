def legacy_17(x):
    return x + 1

def old_helper_17(x):
    return legacy_17(x)

class Unused17:
    def never_17(self):
        return 0

HOOKS_17 = {}

def hook_17(x):
    return x

def call_by_name_17(name, x):
    return globals()[name](x)
