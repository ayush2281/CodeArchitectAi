def legacy_13(x):
    return x + 1

def old_helper_13(x):
    return legacy_13(x)

class Unused13:
    def never_13(self):
        return 0

HOOKS_13 = {}

def hook_13(x):
    return x

def call_by_name_13(name, x):
    return globals()[name](x)
