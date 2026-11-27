def legacy_25(x):
    return x + 1

def old_helper_25(x):
    return legacy_25(x)

class Unused25:
    def never_25(self):
        return 0

HOOKS_25 = {}

def hook_25(x):
    return x

def call_by_name_25(name, x):
    return globals()[name](x)
