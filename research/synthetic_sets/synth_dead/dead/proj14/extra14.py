def legacy_14(x):
    return x + 1

def old_helper_14(x):
    return legacy_14(x)

class Unused14:
    def never_14(self):
        return 0

HOOKS_14 = {}

def hook_14(x):
    return x

def call_by_name_14(name, x):
    return globals()[name](x)
