def legacy_15(x):
    return x + 1

def old_helper_15(x):
    return legacy_15(x)

class Unused15:
    def never_15(self):
        return 0

HOOKS_15 = {}

def hook_15(x):
    return x

def call_by_name_15(name, x):
    return globals()[name](x)
