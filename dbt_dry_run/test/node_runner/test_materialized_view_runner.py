from unittest.mock import MagicMock

from dbt_dry_run.exception import UpstreamFailedException
from dbt_dry_run.models import BigQueryFieldType, Table, TableField
from dbt_dry_run.models.dry_run_result import DryRunResult
from dbt_dry_run.models.report import DryRunStatus
from dbt_dry_run.node_runner.materialized_view_runner import MaterializedViewRunner
from dbt_dry_run.results import Results
from dbt_dry_run.scheduler import ManifestScheduler
from dbt_dry_run.test.utils import SimpleNode, get_executed_sql, A_SQL_QUERY


A_SIMPLE_TABLE = Table(
    fields=[
        TableField(
            name="a",
            type=BigQueryFieldType.STRING,
        )
    ]
)


def test_model_as_materialized_view_run_sql_query() -> None:
    mock_sql_runner = MagicMock()
    mock_sql_runner.query.return_value = (
        DryRunStatus.SUCCESS,
        A_SIMPLE_TABLE,
        None,
    )

    node = SimpleNode(
        unique_id="node1", depends_on=[], resource_type=ManifestScheduler.MODEL
    ).to_node()
    node.depends_on.deep_nodes = []
    node.config.materialized = "materialized_view"

    results = Results()

    model_runner = MaterializedViewRunner(mock_sql_runner, results)
    result = model_runner.run(node)

    assert result.status == DryRunStatus.SUCCESS
    assert result.table
    assert result.table.fields[0].name == A_SIMPLE_TABLE.fields[0].name

    executed_sql = get_executed_sql(mock_sql_runner)
    assert executed_sql == A_SQL_QUERY
    assert node.compiled_code in executed_sql


def test_model_with_failed_dependency_raises_upstream_failed_exception() -> None:
    mock_sql_runner = MagicMock()
    mock_sql_runner.query.return_value = (
        DryRunStatus.SUCCESS,
        A_SIMPLE_TABLE,
        None,
    )

    upstream_simple_node = SimpleNode(unique_id="upstream", depends_on=[])
    upstream_node = upstream_simple_node.to_node()
    upstream_node.depends_on.deep_nodes = []

    node = SimpleNode(
        unique_id="node1",
        depends_on=[upstream_simple_node],
        resource_type=ManifestScheduler.MODEL,
    ).to_node()
    node.depends_on.deep_nodes = ["upstream"]

    results = Results()
    results.add_result(
        "upstream",
        DryRunResult(
            node=upstream_node,
            status=DryRunStatus.FAILURE,
            table=None,
            exception=Exception("BOOM"),
        ),
    )

    model_runner = MaterializedViewRunner(mock_sql_runner, results)
    result = model_runner.run(node)
    assert result.status == DryRunStatus.FAILURE
    assert isinstance(result.exception, UpstreamFailedException)
