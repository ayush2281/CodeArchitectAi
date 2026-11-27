def legacy_37(x):
    return x + 1

def old_helper_37(x):
    return legacy_37(x)

class Unused37:
    def never_37(self):
        return 0

HOOKS_37 = {}

def hook_37(x):
    return x

def call_by_name_37(name, x):
    return globals()[name](x)
