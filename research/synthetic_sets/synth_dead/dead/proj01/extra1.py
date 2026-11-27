def legacy_1(x):
    return x + 1

def old_helper_1(x):
    return legacy_1(x)

class Unused1:
    def never_1(self):
        return 0

HOOKS_1 = {}

def hook_1(x):
    return x

def call_by_name_1(name, x):
    return globals()[name](x)
