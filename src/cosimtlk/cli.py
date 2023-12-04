import logging
from typing import Annotated

import typer
from rich.logging import RichHandler

app = typer.Typer(
    name="cosimtlk",
    help="A tool to simulate FMUs.",
    add_completion=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def main(
    verbose: bool = False,  # noqa
) -> None:
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[RichHandler()])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


@app.command()
def server(
    host: Annotated[str, typer.Option("--host", "-h", help="Host to listen on.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Port to listen on.")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", "-r", help="Reload server on file changes.")] = False,  # noqa
):
    try:
        import uvicorn
    except ImportError:
        typer.echo("Please install uvicorn to run the server.")
    else:
        uvicorn.run("cosimtlk.app.main:app", host=host, port=port, reload=reload)
