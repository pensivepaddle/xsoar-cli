from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import click

from xsoar_cli.utilities.config_file import get_xsoar_config, load_config
from xsoar_cli.utilities.validators import validate_xsoar_connectivity

if TYPE_CHECKING:
    from xsoar_client.xsoar_client import Client

logger = logging.getLogger(__name__)


@click.group(help="Execute commands and automations in XSOAR playground or incidents")
def playground() -> None:
    """Execute commands and automations in XSOAR playground or incidents.

    The playground is a dedicated XSOAR investigation used for testing commands
    without affecting real incidents. You can also target a specific incident ID
    to run commands in that incident's war room.
    """


@click.command()
@click.option("--environment", default=None, help="Environment to use (default from config).")
@click.option(
    "--investigation-id",
    default=None,
    help="Investigation or incident ID to run in. Defaults to the XSOAR playground.",
)
@click.argument("command", type=str)
@click.pass_context
@load_config
@validate_xsoar_connectivity()
def run(ctx: click.Context, environment: str | None, investigation_id: str | None, command: str) -> None:
    """Execute a command or automation in XSOAR.

    COMMAND is the XSOAR command string to execute. Commands must start with '!',
    for example '!Print value=hello' or '!azure-sentinel-list-tables'.

    If --investigation-id is not given the command runs in the XSOAR playground.
    Pass an incident number to run the command in the context of that incident instead.

    Usage examples:

    xsoar-cli playground run '!Print value=hello'

    xsoar-cli playground run --investigation-id 12345 '!MyAutomation arg=value'
    """
    if not command.startswith("!"):
        click.echo("Error: command must start with '!'", err=True)
        ctx.exit(1)
        return

    config = get_xsoar_config(ctx)
    client: Client = config.get_client(environment)

    if investigation_id is None:
        click.echo("Fetching playground ID...", nl=False)
        try:
            investigation_id = _get_playground_id(client)
            click.echo(f"ok. (ID: {investigation_id})")
        except Exception as ex:  # noqa: BLE001
            logger.info("Failed to fetch playground ID: %s", ex)
            click.echo(f"FAILED: {ex!s}")
            ctx.exit(1)
            return

    logger.info(
        "Executing command '%s' in investigation '%s' (environment: '%s')",
        command,
        investigation_id,
        environment or config.default_environment,
    )
    click.echo(f"Executing in investigation {investigation_id}...", nl=False)
    try:
        entries = _execute_command(client, investigation_id=investigation_id, command=command)
        click.echo("ok.")
    except Exception as ex:  # noqa: BLE001
        logger.info("Failed to execute command '%s': %s", command, ex)
        click.echo(f"FAILED: {ex!s}")
        ctx.exit(1)
        return

    _print_entries(entries)


def _get_playground_id(client: Client) -> str:
    """Return the investigation ID of the XSOAR playground.

    Searches for investigations of type 9 (playground) and returns the first result.
    """
    response = client._make_request(  # noqa: SLF001
        endpoint="/investigations/search",
        method="POST",
        json={"filter": {"type": [9]}},
    )
    response.raise_for_status()
    data = response.json()
    investigations = data.get("data") or []
    if not investigations:
        raise ValueError("No playground found. Make sure your account has access to the XSOAR playground.")
    return investigations[0]["id"]


def _execute_command(client: Client, *, investigation_id: str, command: str) -> list[dict]:
    """Execute a command via /entry/execute/sync and return the list of result entries."""
    response = client._make_request(  # noqa: SLF001
        endpoint="/entry/execute/sync",
        method="POST",
        json={"investigationId": investigation_id, "data": command},
    )
    response.raise_for_status()
    return response.json()


def _print_entries(entries: list[dict]) -> None:
    """Print the contents of each result entry to stdout.

    The API returns `contents` (lowercase) in most responses. The capitalised
    `Contents` key appears in some client-side transformations (e.g. the
    nitro_execute_api_command helper from the NVISO blog). Both are checked so
    that callers don't need to normalise the key themselves.
    """
    if not entries:
        click.echo("(no output)")
        return
    for entry in entries:
        contents = entry.get("contents") or entry.get("Contents")
        if contents is None:
            continue
        if isinstance(contents, (dict, list)):
            click.echo(json.dumps(contents, indent=2))
        else:
            click.echo(str(contents))


playground.add_command(run)
