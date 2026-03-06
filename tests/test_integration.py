import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from xsoar_cli import cli

SAMPLE_INTEGRATIONS = [
    {"name": "MyIntegration", "type": "python", "enabled": True},
    {"name": "OtherIntegration", "type": "javascript", "enabled": False},
]


@pytest.fixture
def mock_xsoar_client_integration():  # noqa: ANN201
    with patch("xsoar_client.xsoar_client.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.test_connectivity.return_value = True
        mock_instance.get_integrations.return_value = json.dumps(SAMPLE_INTEGRATIONS)
        mock_client.return_value = mock_instance
        yield mock_instance


class TestIntegration:
    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    @pytest.mark.parametrize(
        ("cli_args", "expected_return_value"),
        [
            (["integration"], 0),
            (["integration", "--help"], 0),
            (["integration", "dumpconfig", "--help"], 0),
        ],
    )
    def test_integration_help(
        self, cli_args: list[str], expected_return_value: int
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.cli, cli_args)
        assert result.exit_code == expected_return_value

    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_dumpconfig_no_args_exits_with_error(
        self, request: pytest.FixtureRequest
    ) -> None:
        request.getfixturevalue("mock_config_file")
        request.getfixturevalue("mock_xsoar_client_integration")
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["integration", "dumpconfig"])
        assert result.exit_code == 1
        assert "Error" in result.output

    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_dumpconfig_by_name_found(self, request: pytest.FixtureRequest) -> None:
        request.getfixturevalue("mock_config_file")
        request.getfixturevalue("mock_xsoar_client_integration")
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["integration", "dumpconfig", "MyIntegration"])
        assert result.exit_code == 0
        output = json.loads(result.output.strip())
        assert output["name"] == "MyIntegration"

    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_dumpconfig_by_name_not_found(self, request: pytest.FixtureRequest) -> None:
        request.getfixturevalue("mock_config_file")
        request.getfixturevalue("mock_xsoar_client_integration")
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["integration", "dumpconfig", "NonExistent"])
        assert result.exit_code == 1
        assert "Cannot find integration instance 'NonExistent'" in result.output

    @patch("pathlib.Path.is_file", MagicMock(return_value=True))
    def test_dumpconfig_all(self, request: pytest.FixtureRequest) -> None:
        request.getfixturevalue("mock_config_file")
        request.getfixturevalue("mock_xsoar_client_integration")
        runner = CliRunner()
        result = runner.invoke(cli.cli, ["integration", "dumpconfig", "--all"])
        assert result.exit_code == 0
        output = json.loads(result.output.strip())
        assert isinstance(output, list)
        assert len(output) == len(SAMPLE_INTEGRATIONS)
        assert output[0]["name"] == "MyIntegration"
        assert output[1]["name"] == "OtherIntegration"
