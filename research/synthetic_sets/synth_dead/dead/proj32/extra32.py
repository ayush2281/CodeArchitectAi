def legacy_32(x):
    return x + 1

def old_helper_32(x):
    return legacy_32(x)

class Unused32:
    def never_32(self):
        return 0

HOOKS_32 = {}

def hook_32(x):
    return x

def call_by_name_32(name, x):
    return globals()[name](x)
