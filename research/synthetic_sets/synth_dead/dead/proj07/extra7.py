def legacy_7(x):
    return x + 1

def old_helper_7(x):
    return legacy_7(x)

class Unused7:
    def never_7(self):
        return 0

HOOKS_7 = {}

def hook_7(x):
    return x

def call_by_name_7(name, x):
    return globals()[name](x)
