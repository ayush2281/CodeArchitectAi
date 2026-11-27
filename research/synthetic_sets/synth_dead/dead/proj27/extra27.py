def legacy_27(x):
    return x + 1

def old_helper_27(x):
    return legacy_27(x)

class Unused27:
    def never_27(self):
        return 0

HOOKS_27 = {}

def hook_27(x):
    return x

def call_by_name_27(name, x):
    return globals()[name](x)
