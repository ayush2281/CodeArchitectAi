def legacy_10(x):
    return x + 1

def old_helper_10(x):
    return legacy_10(x)

class Unused10:
    def never_10(self):
        return 0

HOOKS_10 = {}

def hook_10(x):
    return x

def call_by_name_10(name, x):
    return globals()[name](x)
