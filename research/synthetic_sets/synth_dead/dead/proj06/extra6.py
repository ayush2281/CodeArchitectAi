def legacy_6(x):
    return x + 1

def old_helper_6(x):
    return legacy_6(x)

class Unused6:
    def never_6(self):
        return 0

HOOKS_6 = {}

def hook_6(x):
    return x

def call_by_name_6(name, x):
    return globals()[name](x)
