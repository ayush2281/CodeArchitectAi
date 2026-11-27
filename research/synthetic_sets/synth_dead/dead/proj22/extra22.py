def legacy_22(x):
    return x + 1

def old_helper_22(x):
    return legacy_22(x)

class Unused22:
    def never_22(self):
        return 0

HOOKS_22 = {}

def hook_22(x):
    return x

def call_by_name_22(name, x):
    return globals()[name](x)
