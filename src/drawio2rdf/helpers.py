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


def clear_xml(item: str) -> str:
    """
    Removes surrounding XML tags from a string if present.
    For example: "<font>rdfs.subClassOf</font>" -> "rdfs.subClassOf"
    """
    if isinstance(item, str) and item.startswith("<") and ">" in item and item.endswith(">"):
        # Remove leading tag
        first_close = item.find(">")
        last_open = item.rfind("</")
        if first_close != -1 and last_open != -1 and last_open > first_close:
            return item[first_close + 1 : last_open]
    return item