import re
from time import time 

from N2G import drawio_diagram


def style_as_dict(style: str):
    if style == None or len(style) == "":
        return dict()
    result = dict()
    for property in style.split(";"):
        if property != "":
            try:
                key, value = property.split("=")
            except:
                key, value = property, "true"
            result[key] = value
    return result


# NOTE: Helper
def match_field(text: str) -> tuple:
    name = re.findall(r"^(\w+)\s+", text)[0]
    nulabble = re.findall(r"(NULL|NOT\s+NULL)$", text)[0]
    type = text.replace(name, "").replace(nulabble, "").strip()
    return name, type, nulabble


# Helper
def is_url(string: str):
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return re.match(regex, string) is not None


def clone_diagram(diagram: drawio_diagram, id: str, name: str) -> drawio_diagram:
    duplicated_diagram = drawio_diagram()
    duplicated_diagram.from_xml(diagram.dump_xml())
    diagram.add_diagram(
        id=id,
        name=name,
        height=diagram.current_diagram.get("height"),
        width=diagram.current_diagram.get("width"),
    )
    diagram.current_root = duplicated_diagram.current_root
    diagram.from_xml(diagram.dump_xml())
    diagram.go_to_diagram(diagram_name=name)
    return diagram

def timer_func(func): 
    # This function shows the execution time of  
    # the function object passed 
    def wrap_func(*args, **kwargs): 
        t1 = time() 
        result = func(*args, **kwargs) 
        t2 = time()
        if (t2 - t1) > 0.001:
            print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s') 
        return result 
    return wrap_func 