def legacy_3(x):
    return x + 1

def old_helper_3(x):
    return legacy_3(x)

class Unused3:
    def never_3(self):
        return 0

HOOKS_3 = {}

def hook_3(x):
    return x

def call_by_name_3(name, x):
    return globals()[name](x)
