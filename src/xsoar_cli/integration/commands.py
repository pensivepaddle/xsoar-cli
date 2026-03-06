import json
import logging
from typing import TYPE_CHECKING

import click

from xsoar_cli.utilities import (
    get_xsoar_config,
    load_config,
    validate_xsoar_connectivity,
)

if TYPE_CHECKING:
    from xsoar_client.xsoar_client import Client

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def integration(ctx: click.Context) -> None:
    """(BETA) Save/load integration configuration for an integration instance."""


@click.option(
    "--environment", default=None, help="Default environment set in config file."
)
@click.option(
    "--all",
    "dump_all",
    is_flag=True,
    default=False,
    help="Dump config for all integration instances.",
)
@click.command()
@click.argument("name", type=str, required=False, default=None)
@click.pass_context
@load_config
@validate_xsoar_connectivity()
def dumpconfig(
    ctx: click.Context, environment: str | None, name: str | None, dump_all: bool
) -> None:
    """Dumps integration config to JSON file."""
    if not dump_all and not name:
        click.echo(
            "Error: provide a NAME argument or use --all to dump all integration instances."
        )
        ctx.exit(1)
        return
    config = get_xsoar_config(ctx)
    xsoar_client: Client = config.get_client(environment)
    logger.debug(
        "Dumping integration config (environment: '%s')",
        environment or config.default_environment,
    )
    response = xsoar_client.get_integrations()
    integrations = json.loads(response)
    if dump_all:
        logger.debug(
            "Fetching config for all integration instances (environment: '%s')",
            environment or config.default_environment,
        )
        click.echo(json.dumps(integrations, sort_keys=True, indent=4) + "\n")
        return
    integration_data = next((i for i in integrations if i["name"] == name), None)
    logger.debug(
        "Fetching config for integration name '%s' (environment: '%s')",
        name,
        environment or config.default_environment,
    )
    if not integration_data:
        click.echo(f"Cannot find integration instance '{name}'")
        ctx.exit(1)
    click.echo(json.dumps(integration_data, sort_keys=True, indent=4) + "\n")


@click.option(
    "--environment", default=None, help="Default environment set in config file."
)
@click.command()
@click.argument("name", type=str)
@click.pass_context
@load_config
@validate_xsoar_connectivity()
def loadconfig(
    ctx: click.Context, environment: str | None, name: str, instance_name: str
) -> None:
    """Loads integration config from JSON file."""
    logger.debug("integration loadconfig command not implemented")
    click.echo("Command not implemented")


integration.add_command(dumpconfig)
integration.add_command(loadconfig)
