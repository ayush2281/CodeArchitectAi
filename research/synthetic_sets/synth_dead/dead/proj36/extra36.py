def legacy_36(x):
    return x + 1

def old_helper_36(x):
    return legacy_36(x)

class Unused36:
    def never_36(self):
        return 0

HOOKS_36 = {}

def hook_36(x):
    return x

def call_by_name_36(name, x):
    return globals()[name](x)
