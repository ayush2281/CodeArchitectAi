def legacy_16(x):
    return x + 1

def old_helper_16(x):
    return legacy_16(x)

class Unused16:
    def never_16(self):
        return 0

HOOKS_16 = {}

def hook_16(x):
    return x

def call_by_name_16(name, x):
    return globals()[name](x)
