import logging

import click

from drawio2rdf.rdf import RDFConstructorFromGraffoo
from drawio2rdf.helpers import use_params


logger = logging.getLogger(__name__)


@use_params
def create_diagram(diagram_path: str, diagram_name: str, library_path: str, **_):
    graph = RDFConstructorFromGraffoo(library_path)
    graph.construct(diagram_path, diagram_name)
    return graph


@use_params
def serialize_graph(
    graph: RDFConstructorFromGraffoo, output_path: str, format: str, **_
):
    graph.serialize(output_path, format=format)


def config(**options):
    verbose = options.pop("verbose")

    # if len(options) > 0:
    #     params = ", ".join(options)
    #     raise Exception(f"Parametros inválidos: {params}")

    params = dict(
        format="%(asctime)s [%(levelname)s]: %(pathname)s:%(lineno)d - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )
    if verbose:
        params["level"] = logging.DEBUG

    logging.basicConfig(**params)


@click.command()
@click.option(
    "--diagram_path",
    "-d",
    required=True,
    type=click.Path(exists=True),
    help='The Drawio diagram file path (e.g., "base.drawio").',
)
@click.option(
    "--library_path",
    "-l",
    required=True,
    type=click.Path(exists=True),
    help='The Drawio library file path (e.g., "graffoo v1.1.xml").',
)
@click.option(
    "--diagram_name",
    "-n",
    default=None,
    help='The diagam name (e.g., "CQ28 | Dataset").',
)
@click.option(
    "--output_path",
    "-o",
    required=True,
    type=click.Path(exists=False),
    default="output.ttl",
    help="The file path the result diagam will be stored.",
)
@click.option(
    "--format",
    "-f",
    default="turtle",
    type=click.Choice(
        ["json-ld", "hext", "n3", "nquads", "nt", "trix", "turtle", "xml"],
        case_sensitive=False,
    ),
    help='The serialization format (default: "turtle").',
)
@click.option("--verbose", is_flag=True, help="Show the code execution.")
def cli(**args):
    config(**args)
    graph = create_diagram(**args)
    serialize_graph(graph=graph, **args)


if __name__ == "__main__":
    cli()
