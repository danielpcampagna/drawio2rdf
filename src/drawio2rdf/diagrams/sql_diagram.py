from dataclasses import dataclass
from typing import List
from xml.etree.ElementTree import Element

from .base import Diagram
from .helpers import match_field, style_as_dict

@dataclass
class Field:
    name: str
    type: str
    nullable: bool = False
    is_pk: bool = False
    is_fk: bool = False

    # TODO: Should this class be dependent of REDiagram?
    @staticmethod
    def from_node(node: Element, diagram: "REDiagram"):
        # NOTE: Assuming it always returns two nodes
        pkfk_node, field_node = diagram.get_children_nodes(node.get("id"))
        is_pk = "PK" in pkfk_node.get("value")
        is_fk = "FK" in pkfk_node.get("value")
        # name, type, nullable = re.match(r"(\w+)\s+(\S*)\s+(NULL|NOT\s+NULL)", field_node.get("value")).groups()
        name, type, nullable = match_field(field_node.get("value"))

        return Field(
            name=name,
            type=type,
            nullable=nullable == "NULL",
            is_pk=is_pk,
            is_fk=is_fk,
        )


@dataclass
class Table:
    name: str
    fields: List[Field]

    @staticmethod
    def from_node(node: Element, diagram: "REDiagram"):
        fields = diagram.get_children_nodes(node)
        return Table(name=node.get("label"), fields=list())


@dataclass
class DrawIOTableDecorator:
    properties: dict
    table: Table


@dataclass
class REDiagram(Diagram):
    """Relational Entity Diagram"""

    @property
    def table_nodes(self) -> List[Element]:
        return list(filter(REDiagram._is_table, self.nodes))

    @property
    def field_nodes(self) -> List[Element]:
        return list(filter(REDiagram._is_field, self._diagram.current_root))

    @property
    def relation_nodes(self) -> List[Element]:
        return list(filter(REDiagram._is_relation, self._diagram.current_root))

    @property
    def note_nodes(self) -> List[Element]:
        return list(filter(REDiagram._is_note, self._diagram.current_root))

    @property
    def note_edges(self) -> List[Element]:
        notes_ids = [n.get("id") for n in self.note_nodes]
        return list(
            filter(
                lambda n: n.get("target") in notes_ids or n.get("source") in notes_ids,
                self._diagram.current_root,
            )
        )

    @property
    def tables(self):
        result: List[Table] = list()
        field_nodes = self.field_nodes
        table_nodes = self.table_nodes
        for table in table_nodes:
            node_id = table.get("id")
            table_fields = [
                Field.from_node(f, self)
                for f in field_nodes
                if f.get("parent") == node_id
            ]
            result.append(Table(name=table.get("label"), fields=table_fields))
        return result

    @property
    def tables_decorators(self):
        result: List[Table] = list()
        for node, table in zip(self.table_nodes, self.tables):
            result.append(DrawIOTableDecorator(properties=node.attrib, table=table))
        return result

    # TODO: implement this method
    # @property
    # def relations(self):
    #     result: List[Table] = list()
    #     for edge in field_nodes

    # def delete_node(node_id: str):

    @staticmethod
    def _is_table(node: Element):
        return style_as_dict(node.get("style")).get("shape") == "table"

    @staticmethod
    def _is_field(node: Element):
        return style_as_dict(node.get("style")).get("shape") == "tableRow"

    @staticmethod
    def _is_field_property(node: Element):
        return style_as_dict(node.get("style")).get("shape") == "partialRectangle"

    @staticmethod
    def _is_relation(node: Element):
        return (
            style_as_dict(node.get("style")).get("edgeStyle")
            == "entityRelationEdgeStyle"
        )

    @staticmethod
    def _is_note(node: Element):
        return style_as_dict(node.get("style")).get("shape") == "note"
