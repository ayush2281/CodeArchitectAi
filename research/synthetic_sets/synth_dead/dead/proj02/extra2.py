def legacy_2(x):
    return x + 1

def old_helper_2(x):
    return legacy_2(x)

class Unused2:
    def never_2(self):
        return 0

HOOKS_2 = {}

def hook_2(x):
    return x

def call_by_name_2(name, x):
    return globals()[name](x)
