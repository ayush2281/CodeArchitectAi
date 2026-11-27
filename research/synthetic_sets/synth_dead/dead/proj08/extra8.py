def legacy_8(x):
    return x + 1

def old_helper_8(x):
    return legacy_8(x)

class Unused8:
    def never_8(self):
        return 0

HOOKS_8 = {}

def hook_8(x):
    return x

def call_by_name_8(name, x):
    return globals()[name](x)
