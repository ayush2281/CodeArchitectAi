def legacy_38(x):
    return x + 1

def old_helper_38(x):
    return legacy_38(x)

class Unused38:
    def never_38(self):
        return 0

HOOKS_38 = {}

def hook_38(x):
    return x

def call_by_name_38(name, x):
    return globals()[name](x)
