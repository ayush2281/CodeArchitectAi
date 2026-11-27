def legacy_28(x):
    return x + 1

def old_helper_28(x):
    return legacy_28(x)

class Unused28:
    def never_28(self):
        return 0

HOOKS_28 = {}

def hook_28(x):
    return x

def call_by_name_28(name, x):
    return globals()[name](x)
