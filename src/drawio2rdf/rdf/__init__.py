import re
import uuid
from enum import Enum
from typing import Literal as TLiteral, cast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from xml.etree.ElementTree import Element
from pathlib import Path
import logging

from rdflib import Graph, Literal, namespace as ns

from drawio2rdf.library import Library, get_children, get_label
from drawio2rdf.diagrams.base import Diagram


ValidFormat = TLiteral["json-ld", "hext", "n3", "nquads", "nt", "trix", "turtle", "xml"]
logger = logging.getLogger(__name__)

def is_builtin_namespace(prefix: str = None, url: str = None):
    if prefix is not None:
        return not hasattr(ns, prefix.upper())
    if url is not None:
        return any(ns.split_uri(n)[0] == url for n in get_builtin_namespaces())
    return False

def get_builtin_namespaces() -> list[tuple[str, ns.Namespace | ns.DefinedNamespaceMeta]]:
    return [(k, getattr(ns, k)) for k in dir(ns) if re.match("^[A-Z]+$", k)]

def declare_global_namespaces():
    for ns in get_builtin_namespaces():
        yield f"ns.{str(ns[0])}"

def use_namespace(prefix: str):
    if prefix.upper() in [n[0] for n in get_builtin_namespaces()]:
        return f"ns.{str(prefix).upper()}"
    return prefix

@dataclass
class RDFLibPredicate:
    source: str
    predicate: str
    target: str
    source_namespace: str
    predicate_namespace: str
    target_namespace: str

    def create(self, g: Graph):
        source_id_namespace = (self.source.get("label"), self.source_namespace)
        predicate_id_namespace = (self.predicate.get("label"), self.predicate_namespace)
        target_id_namespace = (self.target.get("label"), self.target_namespace)

        triple = []
        variables = []
        for id, namespace in [source_id_namespace, predicate_id_namespace, target_id_namespace]:
            if is_literal(id):
                item = build_literal(id)
            else:
                id_var, id_label = get_var_label(id, namespace)
                id_var = use_namespace(id_var)
                variables.append(id_var)
                item = f"{id_var}.{id_label}"
            triple.append(item)
                
        triple = ", ".join(triple)
        triple = f"({triple})"
        variables = ", ".join(variables)
        exec(f"g.add({triple})")

@dataclass
class RDFLibNamespace:
    prefix: str
    url: str

    # def __post_init__(self):
    #     if self.prefix == "":
    #         self.prefix = "default"

    @property
    def prefix_var(self):
        return re.sub("-", "_", self.prefix) if self.prefix != "" else "default"
    #     return re.sub("-", "_", self.prefix)

    def create(self, g: Graph):
        exec("from rdflib.namespace import Namespace")
        exec(f'global {self.prefix_var}; {self.prefix_var} = Namespace("{self.url}")')
        exec(f'g.bind("{self.prefix}", {self.prefix_var})')

def as_var(text: str) -> str:
    # TODO: This must be inside some class
    return re.sub(r"\n.*", "", text.replace("-", "_") if not re.match(r"^:\w+", text) else f"default{text}")

def to_camel_case(text: str) -> str:
    s = text.replace("-", " ").replace("_", " ")
    s = s.split()
    if len(text) == 0:
        return text
    return s[0] + ''.join(i.capitalize() for i in s[1:])

@dataclass
class RDFLibClass:
    component: dict

    def create(self, g: Graph, namespace: RDFLibNamespace):
        # TODO: put this block inside a function
        id = self.component["label"]
        superclasses = []
        if "\n" in id:
            id, superclasses = re.sub("[\(\)]", "", self.component["label"]).split("\n")
            superclasses = [s.strip() for s in superclasses.split(",")]
        
            # Fix empty prefixes
            superclasses = [f"{namespace.prefix}{c}" if re.match(r"^:\w+", c) else c for c in superclasses]
        
        id_var, id_label = get_var_label(id, namespace)

        # from rdflib.namespace import RDF
        if is_builtin_namespace(id_var):
            exec(f"g.add(({id_var}.{id_label}, ns.RDF.type, ns.OWL.Class))")
        else:
            exec(f"global {id_var}; g.add(({id_var}.{id_label}, ns.RDF.type, ns.OWL.Class))")

        for superclasse in superclasses:
            sc_prefix, sc_id = superclasse.split(":")
            sc_prefix_var = use_namespace(to_camel_case(as_var(sc_prefix)).upper())
            global_vars = ", ".join([id_var])
            exec(f"global {global_vars}; g.add(({id_var}.{id_label}, ns.RDF.type, {sc_prefix_var}.{sc_id}))")


@dataclass
class RDFLibInstance:
    component: dict
    
    def create(self, g: Graph, namespace: RDFLibNamespace):
        # TODO: put this block inside a function
        id = self.component["label"]
        superclasses = []
        if "\n" in id:
            id, superclasses = re.sub("[\(\)]", "", self.component["label"]).split("\n")
            superclasses = [s.strip() for s in superclasses.split(",")]
        
            # Fix empty prefixes
            superclasses = [f"{namespace.prefix}{c}" if re.match(r"^:\w+", c) else c for c in superclasses]
        
        id_var, id_label = get_var_label(id, namespace)
        global_ns = ", ".join(declare_global_namespaces())

        exec(f"global {id_var}; g.add(({id_var}.{id_label}, ns.RDF.type, ns.OWL.NamedIndividual))")
        for superclasse in superclasses:
            sc_prefix, sc_id = superclasse.split(":")
            sc_prefix_var = use_namespace(to_camel_case(as_var(sc_prefix)))
            global_vars = ", ".join([id_var])
            exec(f"global {global_vars}; g.add(({id_var}.{id_label}, ns.RDF.type, {sc_prefix_var}.{sc_id}))")


@dataclass
class RDFLibOntology:
    elements: list[Element]

    def create(self):
        for element in self.elements:
            RDFLibInstance(element).create()


@dataclass
class ConstructorFromDrawIOLibrary(ABC):
    library_path: str
    library: Library = field(init=False, repr=False)

    def __post_init__(self):
        self.library = Library.from_file(self.library_path)

    def construct(self, path: str, diagram_name: str = None):
        diagram = Diagram.from_drawio(path, diagram_name)
        elements = diagram.all_nodes
        self.g = Graph()
        return self._construct_components(elements)

    # TODO: How to define the return type?
    @abstractmethod
    def _construct_components(self, elements: list[Element]):
        pass


class GraffooEnum(Enum):
    CLASS = "Class"
    DATATYPE = "Datatype"
    CLASS_RESTRICTION = "ClassRestriction"
    INSTANCE = "instance"
    PREDICATE = "predicate"
    OBJECT_PROPERTY = "objectProperty"
    ANNOTATION_PROPERTY_FACILITY = "annotationPropertyFacility"
    ANNOTATION_PROPERTY = "annotationProperty"
    OBJECT_PROPERTY_FACILITY = "objectPropertyFacility"
    DATA_PROPERTY_FACILITY = "dataPropertyFacility"
    DATA_PROPERTY = "dataProperty"
    DATATYPE_INSTANCE = "datatype"
    DATATYPE_RESTRICTION = "DatatypeRestriction"
    ONTOLOGY = "ontology"
    ADDITIONAL_AXIOMS = "additionalAxioms"
    ANNOTATIONS = "annotations"
    SWRL = "SWRL"
    PREFIXES = "Prefixes"

    @staticmethod
    def is_class(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.CLASS.value}\d*", candidate) is not None

    @staticmethod
    def is_datatype(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.DATATYPE.value}\d*", candidate) is not None

    @staticmethod
    def is_class_restriction(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.CLASS_RESTRICTION.value}\d*", candidate) is not None

    @staticmethod
    def is_instance(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.INSTANCE.value}\d*", candidate) is not None

    @staticmethod
    def is_predicate(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.PREDICATE.value}\d*", candidate) is not None

    @staticmethod
    def is_object_property(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.OBJECT_PROPERTY.value}\d*", candidate) is not None

    @staticmethod
    def is_annotation_property_facility(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.ANNOTATION_PROPERTY_FACILITY.value}\d*", candidate) is not None

    @staticmethod
    def is_annotation_property(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.ANNOTATION_PROPERTY.value}\d*", candidate) is not None

    @staticmethod
    def is_object_property_facility(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.OBJECT_PROPERTY_FACILITY.value}\d*", candidate) is not None

    @staticmethod
    def is_data_property_facility(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.DATA_PROPERTY_FACILITY.value}\d*", candidate) is not None

    @staticmethod
    def is_data_property(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.DATA_PROPERTY.value}\d*", candidate) is not None

    @staticmethod
    def is_datatype_instance(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.DATATYPE_INSTANCE.value}\d*", candidate) is not None

    @staticmethod
    def is_datatype_restriction(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.DATATYPE_RESTRICTION.value}\d*", candidate) is not None

    @staticmethod
    def is_ontology(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.ONTOLOGY.value}\d*", candidate) is not None

    @staticmethod
    def is_additional_axioms(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.ADDITIONAL_AXIOMS.value}\d*", candidate) is not None

    @staticmethod
    def is_annotations(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.ANNOTATIONS.value}\d*", candidate) is not None

    @staticmethod
    def is_swrl(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.SWRL.value}\d*", candidate) is not None

    @staticmethod
    def is_prefixes(candidate: str) -> bool:
        return re.match(rf"^{GraffooEnum.PREFIXES.value}\d*", candidate) is not None


class RDFConstructorFromGraffoo(ConstructorFromDrawIOLibrary):

    # TODO: define a structure for these components
    def _construct_components(self, elements: list[Element]):
        components = self.library.generate_components_from_elements(elements)
        logger.info(f"Found components in this library: {', '.join(set(c['category'].category for c in components))}")

        # Create namespaces and bind them
        namespaces = list()
        prefixes = dict()

        # TODO: create a function for this block
        # Add all prefixes firstly
        for component in components:
            if GraffooEnum.is_prefixes(component["category"].category):
                prefix_elem, url_elem = component["children"]
                
                # NOTE: Maybe this might be not enought for all cases
                urls = re.findall(r"((?:www\.|http://|https://)(?:www\.)*.*?(?=(?:www\.|http://|https://|$)))", re.sub("<.*?>", "", url_elem.get("value")))
                prefixes = extract_pattern(r"[\w-]*:", prefix_elem.get("value"))

                for p, u in zip(prefixes, urls):
                    if is_builtin_namespace(p):
                        p = to_camel_case(p)
                        namespace = RDFLibNamespace(p, u)
                        namespace.create(self.g)
                        namespaces.append(namespace)
        for p, u in get_builtin_namespaces():
            namespaces.append(RDFLibNamespace(p, str(u)))

        # Add vertex
        for component in components:
            if GraffooEnum.is_ontology(component["category"].category):
                # TODO: Refactor this block
                onto_components = self.get_ontology_components_from_ontology_component(component)
                onto_namespace = get_component_namespace_from_onto(component, namespaces)
                
                for onto_component in onto_components:
                    if GraffooEnum.is_instance(onto_component["category"].category):
                        RDFLibInstance(onto_component).create(self.g, onto_namespace)
                    elif GraffooEnum.is_class(onto_component["category"].category):
                        RDFLibClass(onto_component).create(self.g, onto_namespace)

        for component in components:
            # TODO: Improve this checking
            if GraffooEnum.is_ontology(component["category"].category):
                onto_components = self.get_ontology_components_from_ontology_component(component)
                onto_namespace = get_component_namespace_from_onto(component, namespaces)
                for onto_component in onto_components:
                    if GraffooEnum.is_predicate(onto_component["category"].category):
                        source_element = [e for e in elements if e.get("id") == onto_component["element"].get("source")][0]
                        target_element = [e for e in elements if e.get("id") == onto_component["element"].get("target")][0]
                        source_component = self.library.generate_components_from_elements([source_element])[0]
                        target_component = self.library.generate_components_from_elements([target_element])[0]
                        source_namespace = get_component_namespace_from_element(source_element, namespaces, components, get_children(source_element.get("id"), elements))
                        target_namespace = get_component_namespace_from_element(target_element, namespaces, components, get_children(target_element.get("id"), elements))
                        predicate_namespace = get_component_namespace_from_element(onto_component["element"], namespaces, components, get_children(onto_component["element"].get("id"), elements))
                        RDFLibPredicate(source_component, onto_component, target_component, source_namespace, predicate_namespace, target_namespace).create(self.g)
            if GraffooEnum.is_predicate(component["category"].category):
                source_element = [e for e in elements if e.get("id") == component["element"].get("source")][0]
                target_element = [e for e in elements if e.get("id") == component["element"].get("target")][0]
                source_component = self.library.generate_components_from_elements([source_element])[0]
                target_component = self.library.generate_components_from_elements([target_element])[0]
                source_namespace = get_component_namespace_from_element(source_element, namespaces, components, get_children(source_element.get("id"), elements))
                target_namespace = get_component_namespace_from_element(target_element, namespaces, components, get_children(target_element.get("id"), elements))
                predicate_namespace = get_component_namespace_from_element(component["element"], namespaces, components, get_children(component["element"].get("id"), elements))
                RDFLibPredicate(source_component, component, target_component, source_namespace, predicate_namespace, target_namespace).create(self.g)

    def get_ontology_components_from_ontology_component(self, component: dict):
        elements = component["children"]
        ontology_components = self.library.generate_components_from_elements(elements)  
        return ontology_components

    def serialize(self, output: str | Path, format: ValidFormat = "turtle"):
        format = cast(ValidFormat, format)
        self.g.serialize(output, format=format)

def extract_pattern(pattern: str, text: str):
    return [prefix[:-1] for prefix in re.findall(pattern, re.sub("<.*?>", "", text))]

def get_component_namespace_from_onto(component: dict, namespaces: list):
    onto_url = component["label"]
    namespace: RDFLibNamespace = [n for n in namespaces if re.search(n.url, onto_url)][0]
    return namespace

def get_component_namespace_from_element(element: Element, namespaces: list, components: list, children: list[Element]):
    if has_prefix(element, children):
        return get_namespace_from_prefix(element, namespaces, children)
    
    element_id = element.get("id")
    for component in components:
        if GraffooEnum.is_ontology(component["category"].category):
            for child in component["children"]:
                if child.get("id") == element_id:
                    return get_component_namespace_from_onto(component, namespaces)
    return None
    # onto_url = component["label"]
    # namespace: RDFLibNamespace = [n for n in namespaces if re.search(n.url, onto_url)][0]
    # return namespace

# TODO: This method should belong a instance that create it
def get_var_label(id: str, namespace: RDFLibNamespace):
    namespace_prefix = use_namespace(namespace.prefix if namespace is not None else "")

    if re.match(r"^:\w+", id):
        id = f"{namespace_prefix}{id}"

    try:
        id_var, id_label = [to_camel_case(s) for s in as_var(id).split(":")]
    except:
        return "default", "TEMP"
    return id_var, id_label

def is_literal(text: str):
    return re.search(r".+(\^{2}.*:.+|@.+)", text) is not None

from rdflib.namespace import XSD
from datetime import datetime
XSD_MAPPER = {
    # XSD.boolean: bool,
    XSD.boolean: str,
    XSD.date: datetime.date,
    XSD.dateTime: lambda d: datetime(*datetime_from_literal(d)),
    XSD.int: int,
}

def datetime_from_literal(text: str):
    return [int(x) for x in re.split(r"[-:T]", text.split("^^")[0].replace("Z", ""))]

def build_literal(text: str):
    clean_literal_text = re.sub(r"<.*?>", "", text)
    if "^^" in clean_literal_text:
        value, type = clean_literal_text.split("^^")
        type_prefix, type_label = type.split(":")
        if type_prefix != "xsd":
            raise Exception(f"Literal must be XSD but was {type_prefix}")
        type = getattr(XSD, type_label)
        result = Literal(XSD_MAPPER[type](value), datatype=type)
    else:
        result = Literal(clean_literal_text)
    return create_var_for_literal(result)

def create_var_for_literal(literal: Literal):
    var = generate_var_name_for(literal)
    exec(f"global {var}; {var} = literal")
    return var

def generate_var_name_for(text: str):
    return f'LITERAL_{str(uuid.uuid3(uuid.NAMESPACE_DNS, text)).replace("-", "_")}'

def has_prefix(element: Element, children: list[Element]):
    element_label: str = get_label(element, children)
    return re.match(r"(\w+:\w+)", re.sub("<.*?>|\n", "", element_label)) is not None

def get_namespace_from_prefix(element: Element, namespaces: list[RDFLibNamespace], children: list[Element]):
    element_label: str = get_label(element, children)
    element_prefix: str = re.findall(r"^(\w+):\w+", re.sub("<.*?>|\n", "", element_label))[0]
    for ns in namespaces:
        if ns.prefix.upper() == element_prefix.upper():
            return ns
    raise Exception(f'There is not Namespace declared for the prefix "{element_prefix}"')
