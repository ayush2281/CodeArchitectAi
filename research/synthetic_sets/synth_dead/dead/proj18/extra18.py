def legacy_18(x):
    return x + 1

def old_helper_18(x):
    return legacy_18(x)

class Unused18:
    def never_18(self):
        return 0

HOOKS_18 = {}

def hook_18(x):
    return x

def call_by_name_18(name, x):
    return globals()[name](x)
