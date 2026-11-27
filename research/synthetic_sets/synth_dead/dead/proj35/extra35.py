def legacy_35(x):
    return x + 1

def old_helper_35(x):
    return legacy_35(x)

class Unused35:
    def never_35(self):
        return 0

HOOKS_35 = {}

def hook_35(x):
    return x

def call_by_name_35(name, x):
    return globals()[name](x)
