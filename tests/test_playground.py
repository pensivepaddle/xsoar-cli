from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from xsoar_cli import cli


class TestPlayground:
    @pytest.mark.parametrize(
        ("cli_args", "expected_return_value"),
        [
            (["playground"], 0),
            (["playground", "--help"], 0),
            (["playground", "run", "--help"], 0),
        ],
    )
    def test_playground_help(self, cli_args: list[str], expected_return_value: int) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.cli, cli_args)
        assert result.exit_code == expected_return_value

    @patch("xsoar_client.xsoar_client.Client")
    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_run_in_playground(self, mock_client: MagicMock, request: pytest.FixtureRequest) -> None:
        """run fetches the playground ID then executes the command."""
        request.getfixturevalue("mock_config_file")

        mock_instance = MagicMock()
        mock_instance.test_connectivity.return_value = True
        mock_client.return_value = mock_instance

        playground_response = MagicMock()
        playground_response.json.return_value = {
            "total": 1,
            "data": [{"id": "test-playground-id", "type": 9, "name": "Playground"}],
        }

        execute_response = MagicMock()
        execute_response.json.return_value = [
            {
                "id": "1@test-playground-id",
                "type": 1,
                "contents": "Hello World",
                "format": "markdown",
                "investigationId": "test-playground-id",
            }
        ]

        mock_instance._make_request.side_effect = [playground_response, execute_response]

        runner = CliRunner()
        result = runner.invoke(cli.cli, ["playground", "run", "!Print value=hello"])
        assert result.exit_code == 0
        assert "test-playground-id" in result.output
        assert "Hello World" in result.output

    @patch("xsoar_client.xsoar_client.Client")
    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_run_with_investigation_id(self, mock_client: MagicMock, request: pytest.FixtureRequest) -> None:
        """run uses the supplied --investigation-id and skips the playground search."""
        request.getfixturevalue("mock_config_file")

        mock_instance = MagicMock()
        mock_instance.test_connectivity.return_value = True
        mock_client.return_value = mock_instance

        execute_response = MagicMock()
        execute_response.json.return_value = [
            {
                "id": "5@12345",
                "type": 1,
                "contents": "Automation output",
                "format": "markdown",
                "investigationId": "12345",
            }
        ]
        mock_instance._make_request.return_value = execute_response

        runner = CliRunner()
        result = runner.invoke(cli.cli, ["playground", "run", "--investigation-id", "12345", "!MyAutomation"])
        assert result.exit_code == 0
        assert "Automation output" in result.output
        # Only the execute call should have been made (no playground lookup)
        assert mock_instance._make_request.call_count == 1

    @patch("xsoar_client.xsoar_client.Client")
    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_run_missing_exclamation_mark(self, mock_client: MagicMock, request: pytest.FixtureRequest) -> None:
        """run exits with an error when the command does not start with '!'."""
        request.getfixturevalue("mock_config_file")

        mock_instance = MagicMock()
        mock_instance.test_connectivity.return_value = True
        mock_client.return_value = mock_instance

        runner = CliRunner()
        result = runner.invoke(cli.cli, ["playground", "run", "--investigation-id", "12345", "Print value=hello"])
        assert result.exit_code != 0

    @patch("xsoar_client.xsoar_client.Client")
    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_run_no_playground_found(self, mock_client: MagicMock, request: pytest.FixtureRequest) -> None:
        """run exits with an error when the playground search returns no results."""
        request.getfixturevalue("mock_config_file")

        mock_instance = MagicMock()
        mock_instance.test_connectivity.return_value = True
        mock_client.return_value = mock_instance

        empty_response = MagicMock()
        empty_response.json.return_value = {"total": 0, "data": []}
        mock_instance._make_request.return_value = empty_response

        runner = CliRunner()
        result = runner.invoke(cli.cli, ["playground", "run", "!Print value=hello"])
        assert result.exit_code != 0

    @patch("xsoar_client.xsoar_client.Client")
    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_run_json_contents(self, mock_client: MagicMock, request: pytest.FixtureRequest) -> None:
        """run pretty-prints JSON contents when the response format is json."""
        request.getfixturevalue("mock_config_file")

        mock_instance = MagicMock()
        mock_instance.test_connectivity.return_value = True
        mock_client.return_value = mock_instance

        execute_response = MagicMock()
        execute_response.json.return_value = [
            {
                "id": "5@12345",
                "type": 1,
                "contents": ["TableA", "TableB"],
                "format": "json",
                "investigationId": "12345",
            }
        ]
        mock_instance._make_request.return_value = execute_response

        runner = CliRunner()
        result = runner.invoke(cli.cli, ["playground", "run", "--investigation-id", "12345", "!azure-sentinel-list-tables raw-response=true"])
        assert result.exit_code == 0
        assert "TableA" in result.output
        assert "TableB" in result.output
