def legacy_30(x):
    return x + 1

def old_helper_30(x):
    return legacy_30(x)

class Unused30:
    def never_30(self):
        return 0

HOOKS_30 = {}

def hook_30(x):
    return x

def call_by_name_30(name, x):
    return globals()[name](x)
