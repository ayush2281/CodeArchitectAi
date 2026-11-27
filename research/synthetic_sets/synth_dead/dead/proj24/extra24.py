def legacy_24(x):
    return x + 1

def old_helper_24(x):
    return legacy_24(x)

class Unused24:
    def never_24(self):
        return 0

HOOKS_24 = {}

def hook_24(x):
    return x

def call_by_name_24(name, x):
    return globals()[name](x)
