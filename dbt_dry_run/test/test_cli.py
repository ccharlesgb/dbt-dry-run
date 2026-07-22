from typing import Any, Dict
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dbt_dry_run.cli import app


class _FakeReporter:
    def report_and_check_results(self) -> int:
        return 0

    def get_report(self) -> Any:
        return None


@pytest.mark.parametrize(
    "vars_arg, expected_vars",
    [
        ("{my_var: 'yaml quoted value'}", {"my_var": "yaml quoted value"}),
        ('{"my_var": "json quoted value"}', {"my_var": "json quoted value"}),
    ],
)
def test_run_accepts_yaml_and_json_quoted_vars(
    vars_arg: str, expected_vars: Dict[str, Any]
) -> None:
    captured_vars: Dict[str, Any] = {}

    def _fake_project_service(args: Any) -> object:
        captured_vars.update(args.vars)
        return object()

    runner = CliRunner()
    with (
        patch("dbt_dry_run.cli.ProjectService", side_effect=_fake_project_service),
        patch("dbt_dry_run.cli.dry_run_manifest", return_value=object()),
        patch("dbt_dry_run.cli.ResultReporter", return_value=_FakeReporter()),
    ):
        result = runner.invoke(app, ["--vars", vars_arg])

    assert result.exit_code == 0
    assert captured_vars == expected_vars
