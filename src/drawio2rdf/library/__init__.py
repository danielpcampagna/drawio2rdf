import re
import json
import base64
import zlib
import urllib.parse
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from dataclasses import dataclass, field
from typing import Literal

from drawio2rdf.diagrams.helpers import style_as_dict
from drawio2rdf.library.model.drawio import MxGraphModel, MxCell


def decompress(compressed_str: str) -> MxGraphModel:
    """decompress
    Decompress compressed MxGraphModel xml string
    Args:
        compressed_str (str): Compressed string
    Returns:
        MxGraphModel: Source MxGraphmOdel
    """

    # NOTE: Some libraries may does not have thier content ("xml" field) compressed.
    # TODO: Maybe exist a way to check the library component content before decompress.
    try:
        compressed_b = base64.b64decode(compressed_str.encode())
        compressed_b = zlib.decompress(compressed_b, wbits=-15)
        xmlstr = urllib.parse.unquote(compressed_b.decode())
        return MxGraphModel(xmlstr)
    except:
        return MxGraphModel(compressed_str)


# Helper
class OrToText(str):
    def __init__(self, *args, **kwargs):
        words = ", ".join(args) + ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        words = words[: words.rindex(",")] + " or" + words[words.rindex(",") + 1 :]
        super().__init__(self, words)


class InvalidMxCellLackingOfPropertiesError(Exception):
    # TODO: Create a exception class for the case of error in line 44
    def __init__(self, lacking_properties: str):
        super().__init__(
            self,
            f"Invalid MxCell attribute. It was expected the properties {lacking_properties}, but they were not found",
        )


@dataclass
class LibraryComponent:
    category: str
    cell: MxCell
    children: list["LibraryComponent"] = field(default_factory=list, repr=False)

    @property
    def style(self):
        return self.cell.style

    @property
    def type(self):
        if getattr(self.cell, "vertex", None) == "1":
            return "vertex"
        elif getattr(self.cell, "edge", None) == "1":
            return "edge"
        else:
            raise InvalidMxCellLackingOfPropertiesError(OrToText(edge="1", vertex="1"))

    @property
    def element(self):
        return self.cell.make_tree().getroot()

    @property
    def has_subgraph(self):
        return "shape=swimlane" in self.cell.get("style")

    def isinstance(self, cell: Element):
        return cell.get(self.type, None) == "1" and cell.get("style") == self.style

    def create(self, element: Element, label: str = None):
        label = label if label else element.get("value")
        return dict(label=label, element=element, category=self)

    def calculate_distance(self, element: Element, children: list[Element]):
        template_element = self.cell.make_tree().getroot()

        # # TODO: Precisa analisar os children
        if len(children) < len(self.children):
            children_distance = float("inf")
        else:
            children_elements = [lc.cell.make_tree().getroot() for lc in self.children]
            children_distance = (
                calculate_distance_between_two_children_considering_children(
                    children, children_elements
                )
            )

        attrs_distance = calculate_distance_between_two_elements_considering_attributes(
            element, template_element, ["vertex", "edge"]
        )
        style_distance = (
            calculate_distance_between_two_elements_considering_style_field(
                element, template_element
            )
        )
        result = sum([children_distance, attrs_distance , style_distance]) / 3
        return result

    def __repr__(self):
        # appendx = "" if len(self.children) == 0 else f', children={self.children}"'
        # return f'{self.__class__.__name__}(category="{self.category}", type="{self.type}{appendx})'
        return f'{self.__class__.__name__}(category="{self.category}", type="{self.type})'

    @staticmethod
    def _from_decompressed_component(component: dict) -> "LibraryComponent":
        graph = decompress(component.get("xml"))
        relevant_cells: list[MxCell] = list()
        for id in graph.get_ids():
            mxcell = graph.find_content(id)
            if "style" in dir(mxcell):
                relevant_cells.append(mxcell)

        tree = make_tree(relevant_cells)
        components = {
            c.id: LibraryComponent(component.get("title"), c) for c in relevant_cells
        }

        for cell in relevant_cells:
            if cell.parent in tree:
                components[cell.parent].children.append(components[cell.id])

        root_ids = find_root_id(tree)
        if len(root_ids) > 1:
            raise Exception("Invalid input because of multiple roots")

        return components[root_ids[0]]


from xml.etree.ElementTree import Element
from library.model.xml_model import XmlObject
from diagrams.base import Diagram


class _ElementConsumer:
    def __init__(self, elements: list[Element]):
        self.elements = elements
        self.consumed_ids = list()

    @property
    def can_iterate(self):
        return self.consumed_ids == len(self.elements)

    @property
    def all_ids(self):
        return [e.get("id") for e in self.elements]

    def consume_elements(self, elements: list[Element]):
        list_of_elements = elements.copy()
        while len(list_of_elements) > 0:
            element = list_of_elements.pop(0)
            _, children = self.consume_element_by_id(element.get("id"))
            list_of_elements.extend(children)

    def consume_element_by_id(self, id: str):
        return self.consume_element_by_index(self.all_ids.index(id))

    def consume_element_by_index(self, index: int):
        children = list()
        element = self.elements.pop(index)
        element_id = element.get("id")
        self.consumed_ids.append(element_id)
        children = get_children(element_id, self.elements)
        return element, children

def get_label(element: Element, children: list[Element]):
    result = element.get("value")
    if result: return result
    for child in children:
        result = child.get("value")
        if result: return result
    import pdb; pdb.set_trace()
    raise Exception(f'Element with id "{element.get("id")}" has no label.')


@dataclass
class Library:
    library_components: dict[str, LibraryComponent] = field(repr=False)

    def create(self, element: Element, children: list[Element] = list()):
        library_component = self.get_closed_library_component(element, children)
        label = get_label(element, children)
        return library_component.create(element, label)

    def get_closed_library_component(self, element: Element, children=None):
        distances: dict[str, float] = dict()
        for category in self.library_components:
            library_component = self.library_components[category]
            distances[category] = library_component.calculate_distance(
                element, children
            )
        result = self.library_components[min(distances, key=distances.get)]
        return result

    def generate_components_from_elements(
        self, elements: list[Element]
    ):
        # NOTE: We are just considering valid elements, that are those with property "style"
        elements = [n for n in elements if "style" in n.keys()]
        candidate_components = aggrupate_elements_by_parenthood(elements)

        result = list()
        for component in candidate_components:
            main_component, *children = component
            created_component = self.generate_component_from_element(main_component, children)
            created_component["children"] = children
            result.append(created_component)
            # TODO: This must be part of the component creationg
        return result

    def generate_component_from_element(
        self, element: Element, children: list[Element]
    ) -> LibraryComponent:
        library_component = self.get_closed_library_component(element, children)
        label = get_label(element, children)
        return library_component.create(element, label)

    def __getattr__(self, name: str):
        return getattr(self.library_components, name)

    def __contains__(self, key):
        return key in self.library_components

    def __getitem__(self, key):
        return self.library_components[key]

    def __setitem__(self, key, value):
        self.library_components[key] = value

    def __delitem__(self, key):
        del self.library_components[key]

    def __len__(self):
        return len(self.library_components)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(components={self.library_components.keys()}>)"
        )

    @staticmethod
    def from_file(file: str):
        raw_components = Library._decompress_library(file)
        components = dict()
        for component in raw_components:
            title = component.get("title")
            lib_comp = LibraryComponent._from_decompressed_component(component)
            components[title] = lib_comp
        return Library(library_components=components)

    @staticmethod
    def _decompress_library(file: str) -> list[dict]:
        return json.loads(ET.parse(file).getroot().text)


def make_tree(cells: list[MxCell]):
    result: dict[str, list[MxCell]] = dict()
    for cell in cells:
        result[cell.id] = list()

    for cell in cells:
        if cell.parent in result:
            result[cell.parent].append(cell)

    # NOTE: Should only consider those cells who have children?
    # result = {id: result[id] for id in result if len(result[id]) > 0}

    return result


def find_root_id(tree: dict[str, list[MxCell]]):
    if not tree:
        return []

    tree = {id: list(map(lambda c: c.id, tree[id])) for id in tree}

    all_ids = set(tree.keys())
    all_children = set(child for children in tree.values() for child in children)

    root_candidates = all_ids - all_children

    if len(tree) == 1 and not any(tree.values()):
        return list(tree.keys())

    return list(root_candidates)


def calculate_distance_between_two_elements_considering_style_field(
    element1: Element, element2: Element
):
    style1_dict = style_as_dict(element1.get("style"))
    style2_dict = style_as_dict(element2.get("style"))

    total_keys = set(style1_dict).union(set(style2_dict))
    total_distance = len(total_keys)
    common_keys = set(style1_dict).intersection(set(style2_dict))
    qty_diff_keys = total_distance - len(common_keys)

    distance = qty_diff_keys
    for key in common_keys:
        if style1_dict[key] != style2_dict[key]:
            # NOTE: In our methodology, if two items have the same keys but
            # different values, the distance between both is a half distance.
            distance += 0.5

    result = distance / total_distance

    return result


def calculate_distance_between_two_children_considering_children(
    children1: list[Element], children2: list[LibraryComponent]
) -> float:
    distance = list()
    for child1, child2 in zip(children1, children2):
        attr_distance = calculate_distance_between_two_elements_considering_attributes(
            child1, child2, ["vertex", "edge"]
        )
        style_distance = (
            calculate_distance_between_two_elements_considering_style_field(
                child1, child2
            )
        )
        distance.append((attr_distance + style_distance) / 2)
    if len(distance) == 0:
        return 0
    return sum(distance) / len(distance)


def calculate_distance_between_two_elements_considering_attributes(
    element1: Element, element2: Element, attributes: list[str]
) -> float:
    # NOTE: The magic numbers are used to ensure the difference in case of lacking attributes
    has_equal_attr = lambda e1, e2, attr: (
        e1.get(attr, float("inf")) == e2.get(attr, e1.get(attr, float("inf")) * -1)
    )
    has_equal_main_attrs = lambda e1, e2: any(
        has_equal_attr(e1, e2, attr) for attr in attributes
    )

    if not has_equal_main_attrs(element1, element2):
        return float("inf")

    return 0


def get_children(
    parent_id: str, elements: list[Element], include_sub=True
) -> list[Element]:
    result = list()
    for element in elements:
        if element.get("parent") == parent_id:
            result.append(element)
            if include_sub:
                result.extend(get_children(element.get("id"), elements))
    return result


def aggrupate_elements_by_parenthood(elements: list[Element]) -> list[list[Element]]:
    result: list[list[Element]] = list()
    was_added = lambda e: any(e in subdiagram for subdiagram in result)
    diagram_index = 0
    for elem in elements:
        if not was_added(elem):
            result.append([elem])
            parent_id = elem.get("id")
            for child in get_children(parent_id, elements):
                if not was_added(child):
                    result[diagram_index].append(child)
            diagram_index += 1
    return result


if __name__ == "__main__":
    library = Library.from_file(".test/graffoo.xml")
