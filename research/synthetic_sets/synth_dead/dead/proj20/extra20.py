def legacy_20(x):
    return x + 1

def old_helper_20(x):
    return legacy_20(x)

class Unused20:
    def never_20(self):
        return 0

HOOKS_20 = {}

def hook_20(x):
    return x

def call_by_name_20(name, x):
    return globals()[name](x)
