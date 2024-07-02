from enum import Enum, auto


class RDFElement(Enum):
    CLASS = auto()
    DATATYPE = auto()
    CLASS_RESTRICTION = auto()
    CLASS_INSTANCE = auto()
    DATATYPE_RESTRICTION = auto()
    ONTOLOGY = auto()
    ADDITIONAL_AXIOMS = auto()
    ANNOTATIONS = auto()
    PREFIXES = auto()
    PREFIXES__PREFIX = auto()
    PREFIXES__URL = auto()
    SWRL_RULES = auto()
    SWRL_RULES__LABEL = auto()
    PREDICATE = auto()
    PREDICATE__LABEL = auto()
    OBJECT_PROPERTY = auto()
    OBJECT_PROPERTY__LABEL = auto()
    ANNOTATION_PROPERTY_FACILITY = auto()
    ANNOTATION_PROPERTY_FACILITY__LABEL = auto()
    ANNOTATION_PROPERTY = auto()
    ANNOTATION_PROPERTY__LABEL = auto()
    OBJECT_PROPERTY_FACILITY = auto()
    OBJECT_PROPERTY_FACILITY__LABEL = auto()
    DATA_PROPERTY_FACILITY = auto()
    DATA_PROPERTY_FACILITY__LABEL = auto()
    DATA_PROPERTY = auto()
    DATA_PROPERTY__LABEL = auto()
    DATATYPE_INSTANCE = auto()


{
    RDFElement.CLASS: {
        "style": "graphMlID=n4;shape=rect;rounded=1;arcsize=30;fillColor=#ffff00;strokeColor=#000000;strokeWidth=1.0",
        "vertex": "1",
    },
    RDFElement.DATATYPE: {
        "style": "graphMlID=n6;shape=parallelogram;fillColor=#ccffcc;strokeColor=#000000;strokeWidth=1.0",
        "vertex": "1",
    },
    RDFElement.CLASS_RESTRICTION: {
        "style": "graphMlID=n5;shape=rect;rounded=1;arcsize=30;fillColor=#ffff99;strokeColor=#000000;strokeWidth=1.0;dashed=1;dashPattern=1 3",
        "vertex": "1",
    },
    RDFElement.CLASS_INSTANCE: {
        "style": "graphMlID=n9;shape=ellipse;fillColor=#ff99cc;strokeColor=#000000;strokeWidth=3.0;verticalAlign=middle;labelPosition=right;verticalLabelPosition=middle;align=left;spacingRight=1;spacing=17;",
        "vertex": "1",
    },
    RDFElement.DATATYPE_RESTRICTION: {
        "style": "graphMlID=n7;shape=parallelogram;fillColor=#ecffec;strokeColor=#000000;strokeWidth=1.0;dashed=1;dashPattern=1 3",
        "vertex": "1",
    },
    RDFElement.ONTOLOGY: {
        "style": "graphMlID=n2;shape=swimlane;startSize=20;rounded=1;arcSize=5;strokeColor=#666699;strokeWidth=1.0;dashed=1;dashPattern=1 3;align=right;fillColor=#99ccff;gradientColor=none;",
        "vertex": "1",
    },
    RDFElement.ADDITIONAL_AXIOMS: {
        "style": "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;darkOpacity=0.05;strokeColor=#A9C4EB;fillColor=#ccffff;gradientColor=none;align=left;spacingLeft=8;",
        "vertex": "1",
    },
    RDFElement.ANNOTATIONS: {
        "style": "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;darkOpacity=0.05;strokeColor=#A9C4EB;fillColor=#ccffff;gradientColor=none;align=left;spacingLeft=8;",
        "vertex": "1",
    },
    RDFElement.PREFIXES: {
        "style": "graphMlID=n0;shape=swimlane;startSize=20;fillColor=#b7b69e;strokeColor=#000000;strokeWidth=1.0;align=right;spacingRight=10;fontStyle=1",
        "vertex": "1",
        "@children": {
            RDFElement.PREFIXES__PREFIX: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;fontFamily=Courier New;",
                "vertex": "1",
            },
            RDFElement.PREFIXES__URL: {
                "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;fontFamily=Courier New;",
                "vertex": "1",
            },
        },
    },
    RDFElement.SWRL_RULES: {
        "style": "graphMlID=n1;shape=swimlane;startSize=20;rounded=1;arcSize=5;strokeColor=#666666;strokeWidth=1.0;dashed=1;dashPattern=5 2;fillColor=#ebebeb;fontColor=#333333;align=right;spacingRight=10;",
        "vertex": "1",
        "@children": {
            RDFElement.SWRL_RULES__LABEL: {
                "style": "text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];autosize=1;fontFamily=Courier New;",
                "vertex": "1",
            }
        },
    },
    RDFElement.PREDICATE: [
        {"style": "rounded=0;orthogonalLoop=1;jettySize=auto;html=1;", "edge": "1"},
        {
            "style": "endArrow=classic;html=1;textDirection=ltr;rounded=0;",
            "edge": "1",
            "@children": {
                RDFElement.PREDICATE__LABEL: {
                    "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;rotation=0;",
                    "vertex": "1",
                }
            },
        },
    ],
    RDFElement.OBJECT_PROPERTY: {
        "style": "graphMlID=e0;rounded=0;endArrow=block;strokeColor=#000080;strokeWidth=1.0;startArrow=oval;startFill=1;endFill=1",
        "edge": "1",
        "@children": {
            RDFElement.OBJECT_PROPERTY__LABEL: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;",
                "vertex": "1",
            }
        },
    },
    RDFElement.ANNOTATION_PROPERTY_FACILITY: {
        "style": "graphMlID=e7;rounded=0;endArrow=open;strokeColor=#993300;dashed=1;dashPattern=1 1;strokeWidth=1.0;startArrow=dash;startFill=1;endFill=1;",
        "edge": "1",
        "@children": {
            RDFElement.ANNOTATION_PROPERTY_FACILITY__LABEL: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;",
                "vertex": "1",
            }
        },
    },
    RDFElement.ANNOTATION_PROPERTY: {
        "style": "graphMlID=e4;rounded=0;endArrow=open;strokeColor=#993300;strokeWidth=1.0;startArrow=dash;startFill=1;endFill=1",
        "edge": "1",
        "@children": {
            RDFElement.ANNOTATION_PROPERTY__LABEL: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;",
                "vertex": "1",
            }
        },
    },
    RDFElement.OBJECT_PROPERTY_FACILITY: {
        "style": "graphMlID=e5;rounded=0;endArrow=block;strokeColor=#000080;dashed=1;dashPattern=1 1;strokeWidth=1.0;startArrow=oval;startFill=1;endFill=1;",
        "edge": "1",
        "@children": {
            RDFElement.OBJECT_PROPERTY_FACILITY__LABEL: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;",
                "vertex": "1",
            }
        },
    },
    RDFElement.DATA_PROPERTY_FACILITY: {
        "style": "graphMlID=e6;rounded=0;endArrow=block;strokeColor=#008000;dashed=1;dashPattern=1 1;strokeWidth=1.0;startArrow=oval;startFill=0;endFill=0;",
        "edge": "1",
        "@children": {
            RDFElement.DATA_PROPERTY_FACILITY__LABEL: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;",
                "vertex": "1",
            }
        },
    },
    RDFElement.DATA_PROPERTY: {
        "style": "graphMlID=e2;rounded=0;endArrow=block;strokeColor=#008000;strokeWidth=1.0;startArrow=oval;startFill=0;endFill=0",
        "edge": "1",
        "@children": {
            RDFElement.DATA_PROPERTY__LABEL: {
                "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];labelBackgroundColor=#ffffff;",
                "vertex": "1",
            }
        },
    },
    RDFElement.DATATYPE_INSTANCE: {
        "style": "text;html=1;spacing=0;align=left;fontFamily=dialog;fontSize=16;fontStyle=0;fontColor=#000000",
    },
}
