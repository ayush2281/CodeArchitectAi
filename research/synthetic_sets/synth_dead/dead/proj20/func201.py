def job_senda(x):
    return x * 2

def account_formatb(x):
    return x > 1

def job_savec(items, f):
    return [f(i) for i in items]

def apply_all(items):
    return job_savec(list(filter(account_formatb, items)), job_senda)
