def legacy_4(x):
    return x + 1

def old_helper_4(x):
    return legacy_4(x)

class Unused4:
    def never_4(self):
        return 0

HOOKS_4 = {}

def hook_4(x):
    return x

def call_by_name_4(name, x):
    return globals()[name](x)
