import re
from dataclasses import dataclass, field
from typing import List, Any, Union
from xml.etree.ElementTree import Element

from .base import Diagram
from .helpers import style_as_dict, is_url

class StrDatatypeId(str):
    @property
    def data(self):
        return re.findall(r'\"(.+)\"\W+\w+', self)[0]
    
    @property
    def sep(self):
        return re.findall(r'\".+\"(\W+)\w+', self)[0]
    
    @property
    def type(self):
        return re.findall(r'\".+\"\W+(\w+)', self)[0]

    @staticmethod
    def has_datatype_format(value: str) -> bool:
        return re.match(r".+(\^\^\w+:\w+|@\w+)", value) is not None

class PrefixLabelId(str):
    @property
    def prefix(self):
        return re.findall(r"([^:]*):", self)[0]
    
    @property
    def label(self):
        return re.findall(r"[^:]*:(.+)", self)[0]


@dataclass
class Relation:
    _element: Element = field(repr=False)
    _ontology: "Ontology" = field(repr=False)

    @property
    def id(self):
        return PrefixLabelId(self._element.get("value"))

    @property
    def target_id(self):
        return self._element.get("target")

    @property
    def source_id(self):
        return self._element.get("source")

    @property
    def target_element(self):
        return self._ontology._diagram.get_node_by_id(self.target_id)

    @property
    def source_element(self):
        return self._ontology._diagram.get_node_by_id(self.source_id)

    @property
    def target(self):
        return self._ontology.get_vertex_by_element_id(self.target_id)

    @property
    def source(self):
        return self._ontology.get_vertex_by_element_id(self.source_id)

    @classmethod
    def from_element(cls, element: Element, ontology: "Ontology"):
        result = cls(_element=element, _ontology=ontology)
        return result

    def __repr__(self):
        source_id = self.source.id if self.source else None
        target_id = self.target.id if self.target else None
        return (
            f"Relation(id={self.id}, source={source_id}, target={target_id})"
        )

    # def __getattr__(self, name: str) -> Any:
    #     name = name.replace("_", ":")
    #     if self.target.id == name:
    #         return self.target

@dataclass
class Predicate(Relation):
    def __repr__(self):
        return (
            f"Predicate(id={self.id}, source={self.source.id}, target={self.target.id})"
        )

@dataclass
class Property(Relation):
    @property
    def id(self):
        element_label = self._ontology._diagram.get_children_nodes(self._element.get("id"))[0]
        clean_id = re.sub(r"<.*?>", "", element_label.get("value").replace("\n", "\\n"))
        if clean_id.startswith(":"):
            clean_id = self._ontology.prefix + clean_id[1:]
        return PrefixLabelId(clean_id)

    def __repr__(self):
        return (
            f"Property(id={self.id}, source={self.source.id}, target={self.target.id})"
        )


from abc import ABC


@dataclass
class ABCVertex(ABC):
    _id: str = field(init=False, repr=True)
    _element: Element | None = field(repr=False, default=None)
    _ontology: "Ontology" = field(repr=False, default=None)

    @property
    def id(self):
        if self._id is None:
            self.__post_init__()
        return PrefixLabelId(self._id)

    @property
    def relations(self):
        return self.relations_from + self.relations_to

    @property
    def relations_to(self):
        return self._ontology.relations_to_node(self._element.get("id"))

    @property
    def relations_from(self):
        return self._ontology.relations_from_node(self._element.get("id"))

    @classmethod
    def from_element(
        cls,
        element: Element,
        ontology: "Ontology",
    ):
        return cls(_element=element, _ontology=ontology)

    def to_turtle(self):
        return self._element.get("value")

    # def __getattr__(self, name: str) -> Any:
    #     name = name.replace("_", ":")
    #     return [r for r in self.relations_to if r.id == name]


@dataclass
class NamedInstace(ABCVertex):
    _types: List[str] = field(init=False, repr=True)

    def __post_init__(self):
        if self._ontology is not None:
            prefix = self._ontology.prefix

        if prefix is not None:
            prefix = prefix.replace(":", "")

        self._id, self._types = NamedInstace._get_id_types_from_compacted_element(
            self._element, prefix
        )

    @property
    def types(self):
        if self._types is None:
            self.__post_init__()
        return self._types

    def to_turtle(self) -> str:
        types = ["owl:NamedIndividual"] + (self.types or [])
        types = list(filter(lambda x: x, types))
        relations: list = [
            f"{'': <{len(self.id)}} {r.id} {r.target.id}" for r in self.relations_from
        ]
        result = (
            " ;\n".join([f"{self.id} rdf:type {', '.join(types)}"] + relations) + " ."
        )

        # TODO: Refactor this block
        url = (
            self._ontology.url
            if not self._ontology.url.endswith("#")
            else self._ontology.url[0:-1]
        )
        id = self.id[self.id.index(":") + 1 :]
        return f"### {url}#{id}\n" f"{result}"

    # TODO: It seems this method belongs to helpers module
    @staticmethod
    def _get_id_types_from_compacted_element(
        node_element: Element, prefix: str
    ) -> tuple[str, list[str]]:
        value = node_element.get("value").replace("\n", "")
        id, _, subclasses = re.findall(r"([^\(]+)\n?(\(([^\)]+)\))?", value)[0]
        subclasses = [c.strip() for c in subclasses.split(",")]

        if ":" not in id:
            id = f":{id}"

        if id.startswith(":"):
            id = f"{prefix}{id}"  # format: "prefix:id"
        # If it's not starting with number
        # elif not re.findall(r"^\d", id):
        #     id_prefix, _ = id.split(":")
        #     assert id_prefix == prefix
        # else:
        #     id = f"{id}^^{prefix}"
        return id, subclasses

    @classmethod
    def from_compacted_element(
        node_element: Element,
        ontology: "Ontology" = None,
    ):
        return NamedInstace(_element=node_element, _ontology=ontology)

    def __repr__(self):
        return f"NamedInstace(id='{self.id}', types=['{self.id}'])"


@dataclass
class Class(ABCVertex):
    _id: str = field(init=False, repr=True)
    _subclass_of: List[str] = field(init=False, repr=True)

    def __post_init__(self):
        if self._ontology is not None:
            prefix = self._ontology.prefix

        if prefix is not None:
            prefix = prefix.replace(":", "")

        self._id, self._subclass_of = Class._get_id_subclasses_from_compacted_element(
            self._element, prefix
        )

    @property
    def subclass_of(self):
        if self._subclass_of is None:
            self.__post_init__()
        return self._subclass_of

    def to_turtle(self) -> str:
        subclasses = self._subclass_of or []
        subclasses = list(filter(lambda x: x, subclasses))
        if len(subclasses) > 0:
            subclasses = [
                f"{'': <{len(self.id)}} rdfs:subClassOf {', '.join(subclasses)}"
            ]
        # try:
        relations: list = [
            f"{'': <{len(self.id)}} {r.id} {r.target.id}"
            for r in self.relations_from
        ]
        # except:
        #     # :generatesData
        #     import pdb

        #     pdb.set_trace()
        #     relations: list = [
        #         f"{'': <{len(self.id)}} {r.id} {r.target.id}"
        #         for r in self.relations_from
        #     ]
        result = (
            " ;\n".join([f"{self.id} rdf:type owl:Class"] + subclasses + relations)
            + " ."
        )

        # TODO: Componentize this block
        url = (
            self._ontology.url
            if not self._ontology.url.endswith("#")
            else self._ontology.url[0:-1]
        )
        id = self.id[self.id.index(":") + 1 :]
        return f"### {url}#{id}\n" f"{result}"

    # TODO: It seems this method belongs to helpers module
    @staticmethod
    def _get_id_subclasses_from_compacted_element(
        node_element: Element, prefix: str
    ) -> tuple[str, list[str]]:
        value = node_element.get("value").replace("\n", "")
        id, _, subclasses = re.findall(r"([^\(]+)\n?(\(([^\)]+)\))?", value)[0]
        subclasses = [c.strip() for c in subclasses.split(",") if len(c.strip()) > 0]

        if ":" not in id:
            id = f":{id}"

        if id.startswith(":"):
            id = f"{prefix}{id}"  # format: "prefix:id"
        # If it's not starting with number
        # elif not re.findall(r"^\d", id):
        #     id_prefix, _ = id.split(":")
        #     assert id_prefix == prefix
        # else:
        #     id = f"{id}^^{prefix}"
        return id, subclasses

    @classmethod
    def from_compacted_element(
        node_element: Element,
        ontology: "Ontology" = None,
    ):
        return Class(_element=node_element, _ontology=ontology)

    def __repr__(self):
        if len(self.subclass_of) == 0:
            return f"Class(id='{self.id}')"
        return f"Class(id='{self.id}', subclasses={self._subclass_of})"


@dataclass
class Datatype(ABCVertex):
    @property
    def id(self):
        clean_id = re.sub(r"<.*?>", "", self._element.get("value").replace("\n", "\\n"))
        if "@" in clean_id:
            sep = "@"
        elif "^^" in clean_id:
            sep = "^^"
        else:
            clean_id, sep = f"{clean_id}@en", "@"
        data, type = clean_id.split(sep)
        return StrDatatypeId(f'"{data}"{sep}{type}')

    def __repr__(self):
        return f"Datatype(id='{self.id}')"

    # def __getattr__(self, name: str) -> Any:
    #     name = name.replace("_", ":")
    #     return [r for r in self.relations_to if r.id == name]


@dataclass
class Prefix:
    data: dict

    def to_turtle(self):
        result = "\n".join(
            [f"@prefix {prefix} <{url}> ." for prefix, url in self.data.items()]
        )
        return result

    @staticmethod
    def from_compact_element(node: Element, diagram: "RDFDiagram") -> "Prefix":
        node_id = node.get("id")
        prefixes, urls = diagram.get_children_nodes(node_id)
        prefixes = re.findall(r"([^:]*:)", re.sub(r"<.*?>", "", prefixes.get("value")))
        # TODO: Improve this code by put into a helper method
        raw_urls = re.split(r"(\w+://)", re.sub(r"<.*?>", "", urls.get("value")))[1:]
        urls = list()
        for i in range(0, len(raw_urls), 2):
            urls.append(raw_urls[i] + raw_urls[i + 1])
        # urls = [re.sub(r"<.*?>", "", u) for u in urls.get("value").split("<br>")]

        params = dict(zip(prefixes, urls))
        return Prefix(data=params)


@dataclass
class Ontology:
    url: str = field(init=False)
    prefix: str = field(init=False)
    _element: Element = field(repr=False)
    _diagram: "RDFDiagram" = field(repr=False)
    named_instances: List[NamedInstace] = field(repr=False, default_factory=list)
    classes: List[Class] = field(repr=False, default_factory=list)
    datatypes: List[Datatype] = field(repr=False, default_factory=list)
    relations: List[Relation] = field(repr=False, default_factory=list)
    properties: List[Property] = field(repr=False, default_factory=list)
    predicates: List[Predicate] = field(repr=False, default_factory=list)

    @property
    def nodes_ids(self):
        return [n.get("id") for n in self._diagram.get_children_nodes(self._element.get("id"))]

    def __post_init__(self):
        url = re.sub(r"(</?\w+>|<|>)", "", self._element.get("value"))
        prefixes = self._diagram.prefixes

        # TODO: This part must be rewrited
        prefix = ":"
        if url in prefixes.data.values():
            prefix_index = list(prefixes.data.values()).index(url)
            prefix = list(prefixes.data.keys())[prefix_index]

        self.url = url
        self.prefix = prefix

        self.classes = self._diagram.get_classes_children_of(self._element, self)
        self.named_instances = self._diagram.get_named_instances_children_of(self._element, self)
        self.datatypes = self._diagram.get_datatypes_children_of(self._element, self)
        self.relations = self._diagram.get_relations_children_of(self._element, self)
        self.properties = self._diagram.get_properties_children_of(self._element, self)
        self.predicates = self._diagram.get_predicates_children_of(self._element, self)

    def get_relations(self, node: Element | str, node_position: str) -> list[Relation]:
        if isinstance(node, Element):
            node = node.get("id")

        result: list[Relation] = list()
        for edge in self._diagram.get_edges_by_node_id(node, node_position=node_position):
            onto = self._diagram.get_ontology_contains_element_id(edge.get("id"))
            if onto is None: continue
            result.append(Relation.from_element(edge, onto))
        
        return result

    def relations_from_node(self, node: Element | str) -> list[Relation]:
        return self.get_relations(node, "source")
    
    def relations_to_node(self, node: Element | str) -> list[Relation]:
        return self.get_relations(node, "target")

    def get_vertex_by_element_id(
        self, element_id: str
    ) -> Union[NamedInstace, Datatype, Class]:
        return (
            self.get_class_by_element_id(element_id)
            or self.get_named_instance_by_element_id(element_id)
            or self.get_datatype_by_element_id(element_id)
        )

    def get_class_by_element_id(self, element_id: str) -> NamedInstace:
        result = [n for n in self.classes if n._element.get("id") == element_id]
        if len(result) > 0:
            return result[0]
        return None

    def get_named_instance_by_element_id(self, element_id: str) -> NamedInstace:
        result = [n for n in self.named_instances if n._element.get("id") == element_id]
        if len(result) > 0:
            return result[0]
        return None

    def get_datatype_by_element_id(self, element_id: str) -> Datatype:
        result = [n for n in self.datatypes if n._element.get("id") == element_id]
        if len(result) > 0:
            return result[0]
        return None

    # TODO: Refactor this code removing this dependency to RDFTurtleDiagram
    @staticmethod
    def from_element(node: Element, diagram: "RDFDiagram") -> "Ontology":
        result = Ontology(node, diagram)
        # result.classes = result._diagram.get_classes_children_of(result._element, result)
        # result.named_instances = result._diagram.get_named_instances_children_of(result._element, result)
        # result.datatypes = result._diagram.get_datatypes_children_of(result._element, result)
        return result


@dataclass
class RDFDiagram(Diagram):

    @property
    def nodes_ids(self) -> List[str]:
        dataset_node = self.get_nodes_by_property("isDataSet")[0]
        children = self.get_children_nodes(dataset_node.get("id"))
        return [n.get("id") for n in children]

    @property
    def edges_ids(self) -> List[str]:
        dataset_node = self.get_nodes_by_property("isDataSet")[0]
        children = self.get_children_nodes(dataset_node.get("id"))
        children_edges = list()
        for node in children:
            children_edges.extend(self.get_edges_by_node_id(node.get("id")))
        return list(set(e.get("id") for e in children_edges))

    @property
    def prefixes_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_prefixes_definition, self.nodes))

    @property
    def dataset(self) -> List[Element]:
        return list(filter(RDFDiagram._is_dataset, self.nodes))

    @property
    def named_instance_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_named_instance, self.nodes))

    @property
    def class_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_class, self.nodes))

    @property
    def datatype_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_datatype, self.nodes))

    @property
    def relation_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_relation, self.edges))
    
    @property
    def predicate_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_predicate, self.relation_nodes))
    
    @property
    def property_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_property, self.relation_nodes))

    @property
    def ontology_nodes(self) -> List[Element]:
        return list(filter(RDFDiagram._is_ontology, self.nodes))

    @property
    def named_instances(self) -> List[NamedInstace]:
        result = list()
        for ontology in self.ontologies:
            result.extend(ontology.named_instances)
        return result
        # return list(map(Instace.from_compact_node, self.nodes))

    @property
    def classes(self) -> List[Class]:
        result = list()
        for ontology in self.ontologies:
            result.extend(ontology.classes)
        return result

    @property
    def datatypes(self):
        result = list()
        for ontology in self.ontologies:
            result.extend(ontology.datatypes)
        return result

    @property
    def prefixes(self) -> Prefix:
        return list(
            map(lambda i: Prefix.from_compact_element(i, self), self.prefixes_nodes)
        )[0]

    @property
    def ontologies(self) -> List[Ontology]:
        return list(map(lambda i: Ontology.from_element(i, self), self.ontology_nodes))
    
    @property
    def relations(self) -> List[Relation]:
        result = list()
        for ontology in self.ontologies:
            result.extend(ontology.relations)
        return result
    
    @property
    def predicates(self) -> List[Predicate]:
        result = list()
        for ontology in self.ontologies:
            result.extend(ontology.predicates)
        return result
    
    @property
    def properties(self) -> List[Property]:
        result = list()
        for ontology in self.ontologies:
            result.extend(ontology.properties)
        return result

    @staticmethod
    def _to_turtle_section(section_name: str):
        return (
            "\n\n\n"
            "#################################################################\n"
            f"#    {section_name.capitalize()}\n"
            "#################################################################"
            "\n\n\n"
        )

    def to_turtle(self, filepath: str = None):
        result = self.prefixes.to_turtle()
        result += RDFDiagram._to_turtle_section("Annotation properties")
        result += RDFDiagram._to_turtle_section("Object Properties")
        result += RDFDiagram._to_turtle_section("Classes")
        result += "\n\n\n".join(i.to_turtle() for i in self.classes)
        result += RDFDiagram._to_turtle_section("Individuals")
        result += "\n\n\n".join(i.to_turtle() for i in self.named_instances)

        if filepath is None:
            return result
        with open(filepath, "w") as f:
            f.write(result)

    def _get_children_by_filter(self, element: Element, key: callable) -> List[Element]:
        return list(filter(key, self.get_children_nodes(element.get("id"))))

    def _map_children_to(self, children: list[Element], cls, *args, **kwargs):
        return list(map(lambda e: cls(e, *args, **kwargs), children))

    def get_class_elements_children_of(self, node: Element) -> List[Element]:
        return self._get_children_by_filter(node, self._is_class)

    def get_classes_children_of(self, element: Element, *args, **kwargs) -> list[Class]:
        return self._map_children_to(
            self._get_children_by_filter(element, self._is_class),
            Class,
            *args,
            **kwargs,
        )
    
    def get_named_instance_elements_children_of(self, node: Element) -> List[Element]:
        return self._get_children_by_filter(node, self._is_named_instance)

    def get_named_instances_children_of(
        self, element: Element, *args, **kwargs
    ) -> list[NamedInstace]:
        return self._map_children_to(
            self.get_named_instance_elements_children_of(element),
            NamedInstace,
            *args,
            **kwargs,
        )

    def get_datatype_elements_children_of(self, node: Element) -> List[Element]:
        return self._get_children_by_filter(node, self._is_datatype)

    def get_datatypes_children_of(
        self, element: Element, *args, **kwargs
    ) -> list[Datatype]:
        return self._map_children_to(
            self.get_datatype_elements_children_of(element),
            Datatype,
            *args,
            **kwargs,
        )
    
    def get_relation_elements_children_of(self, node: Element) -> List[Element]:
        return self._get_children_by_filter(node, self._is_relation)

    def get_relations_children_of(
        self, element: Element, *args, **kwargs
    ) -> list[Relation]:
        return self._map_children_to(
            self.get_relation_elements_children_of(element),
            Relation,
            *args,
            **kwargs,
        )
    
    def get_predicate_elements_children_of(self, node: Element) -> List[Element]:
        return self._get_children_by_filter(node, self._is_predicate)

    def get_predicates_children_of(
        self, element: Element, *args, **kwargs
    ) -> list[Predicate]:
        return self._map_children_to(
            self.get_predicate_elements_children_of(element),
            Predicate,
            *args,
            **kwargs,
        )
    
    def get_property_elements_children_of(self, node: Element) -> List[Element]:
        return self._get_children_by_filter(node, self._is_property)

    def get_properties_children_of(
        self, element: Element, *args, **kwargs
    ) -> list[Property]:
        return self._map_children_to(
            self.get_property_elements_children_of(element),
            Property,
            *args,
            **kwargs,
        )

    def get_ontology_contains_element_id(self, id: str, only_existent: bool = True) -> Ontology | None:
        for onto in self.ontologies:
            if id in onto.nodes_ids:
                return onto
        if only_existent:
            return None
        return self._build_ontology_from_element(self.get_node_by_id(id))

    def get_named_instances_by_element_id(self, id: str) -> NamedInstace | None:
        for named_instance in self.named_instances:
            if named_instance.id == id:
                return named_instance
        return None

    def _build_ontology_from_element(self, element: Element) -> Ontology:
        prefix, _ = re.findall(r"([^:]*:)(.+)", element.get("value"))[0]
        return Ontology(None, self, )

    @staticmethod
    def _is_prefixes_definition(node: Element):
        return (
            style_as_dict(node.get("style")).get("shape") == "swimlane"
        ) and node.get("value").upper() == "PREFIXES"

    @staticmethod
    def _is_dataset(node: Element):
        return (
            node.get("vertex") == "1"
            and style_as_dict(node.get("style")).get("shape") == "swimlane"
            and node.get("value").upper() != "PREFIXES"
        )

    @staticmethod
    def _is_named_instance(node: Element) -> bool:
        styles = style_as_dict(node.get("style"))
        return (
            node.get("vertex") == "1"
            and styles.get("shape") == "ellipse"
            and (styles.get("text", "false") == "false")
        )

    @staticmethod
    def _is_datatype(node: Element) -> bool:
        styles = style_as_dict(node.get("style"))
        return (
            node.get("vertex") == "1"
            and StrDatatypeId.has_datatype_format(node.get("value"))
            and styles.get("shape", None) is None
            and (styles.get("text", "false") == "true")
        )

    @staticmethod
    def _is_class(node: Element) -> bool:
        styles = style_as_dict(node.get("style"))
        return (
            node.get("vertex") == "1"
            and styles.get("shape") == "rect"
            and (styles.get("text", "false") == "false")
        )

    @staticmethod
    def _is_relation(node: Element) -> bool:
        # return style_as_dict(node.get("style")).get("edge") == "1"
        return node.get("edge") == "1"
    
    @staticmethod
    def _is_predicate(node: Element) -> bool:
        styles = style_as_dict(node.get("style"))
        return (
            RDFDiagram._is_relation(node)
            and styles.get("edgeStyle") == "orthogonalEdgeStyle"
            and styles.get("shape") == "connector"
            and styles.get("endArrow") == "classic"
            and styles.get("startArrow", None) is None
        )
    
    @staticmethod
    def _is_property(node: Element) -> bool:
        styles = style_as_dict(node.get("style"))
        return (
            RDFDiagram._is_relation(node)
            and styles.get("startArrow") == "oval"
            and styles.get("endArrow") == "block"
        )

    @staticmethod
    def _is_ontology(node: Element) -> bool:
        return (
            node.get("vertex") == "1"
            and style_as_dict(node.get("style")).get("shape") == "swimlane"
            and is_url(re.sub(r"(</?\w+>|<|>)", "", node.get("value")))
        )
