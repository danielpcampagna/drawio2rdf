import functools
import inspect


# def use_params(params: list[str]):
#     def wrapper(f):
#         functools.wraps
#         def inner(**kwargs):
#             fparams = {k: kwargs.pop(k) for k in params}
#             return f(**fparams)
#         return inner
#     return wrapper


def use_params(f):
    functools.wraps
    def inner(**kwargs):
        params = inspect.getfullargspec(f)[0]
        fparams = {k: kwargs.pop(k) for k in params}
        return f(**fparams)
    return inner