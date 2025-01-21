from dataclasses import dataclass
from typing import List, cast
from xml.etree.ElementTree import Element

# from N2G import drawio_diagram

from .tmp_n2g import drawio_diagram # NOTE: Until the approvation of this [PR](https://github.com/dmulyalin/N2G/pull/32), this is necessary for correct results
from .typings import TYPE_VALID_NODE_POSITIONS


@dataclass
class Diagram:
    _diagram: drawio_diagram

    @property
    def nodes_ids(self) -> List[str]:
        return self._diagram.nodes_ids[self._diagram.current_diagram_id]

    @property
    def edges_ids(self) -> List[str]:
        return self._diagram.edges_ids[self._diagram.current_diagram_id]

    @property
    def nodes(self) -> List[Element]:
        return [self.get_node_by_id(node_id) for node_id in self.nodes_ids]

    @property
    def all_nodes(self) -> List[Element]:
        return [node for node in self._diagram.current_root]

    @property
    def edges(self) -> List[Element]:
        result = list()
        for edge_id in self.edges_ids:
            result.append(self.get_node_by_id(edge_id))
            # result.extend(self.get_edges_by_node_id(edge_id, "both"))
        return result

    def get_node_by_id(self, id: str) -> Element | None:
        result = self.get_nodes_by_property("id", id)
        if len(result) > 0:
            return result[0]
        raise Exception(f"Not found a node with id {id}")

    def get_nodes_by_property(
        self, property_name: str, value: str = None
    ) -> List[Element]:
        result = list()
        for node in self._diagram.current_root:
            if property_name in node.keys():
                if value is None:
                    result.append(node)
                    continue
                if node.get(property_name) == value:
                    result.append(node)
        return result

    def get_edge_by_id(self, id: str) -> Element | None:
        try:
            self.get_node_by_id(id)
        except:
            raise Exception(f"Not found a edge with id {id}")

    def get_edges_by_node_id(
        self, node_id: str, node_position: TYPE_VALID_NODE_POSITIONS = "both"
    ) -> list[Element]:
        node_position = cast(TYPE_VALID_NODE_POSITIONS, node_position)
        result = list()
        for node in self._diagram.current_root:
            if node_position in ["source", "both"] and node.get("source") == node_id:
                result.append(node)
            if node_position in ["target", "both"] and node.get("target") == node_id:
                result.append(node)
        return result

    def get_children_nodes(self, parent_id: str, include_sub=True) -> List[Element]:
        result = list()
        for node in self._diagram.current_root:
            if node.get("parent") == parent_id:
                result.append(node)
                if include_sub:
                    result.extend(self.get_children_nodes(node.get("id")))
        return result
    
    @classmethod
    def from_drawio(cls, path: str, diagram_name: str = None):
        diagram = drawio_diagram()
        diagram.from_file(path)

        if diagram_name is not None:
            diagram.go_to_diagram(diagram_name=diagram_name)

        return cls(diagram)
