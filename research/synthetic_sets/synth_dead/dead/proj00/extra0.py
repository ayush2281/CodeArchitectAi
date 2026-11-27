def legacy_0(x):
    return x + 1

def old_helper_0(x):
    return legacy_0(x)

class Unused0:
    def never_0(self):
        return 0

HOOKS_0 = {}

def hook_0(x):
    return x

def call_by_name_0(name, x):
    return globals()[name](x)
