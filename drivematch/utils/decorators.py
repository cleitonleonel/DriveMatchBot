def handler(func):
    func.is_handler = True
    return func
