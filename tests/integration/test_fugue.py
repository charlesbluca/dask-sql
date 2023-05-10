import dask.dataframe as dd
import pandas as pd
import pytest

from dask_sql import Context
from tests.utils import assert_eq

fugue_sql = pytest.importorskip("fugue_sql")

from dask_sql.integrations.fugue import fsql_dask  # noqa: E402


def test_fugue_workflow(client):
    dag = fugue_sql.FugueSQLWorkflow()
    df = dag.df([[0, "hello"], [1, "world"]], "a:int64,b:str")
    dag("SELECT * FROM df WHERE a > 0 YIELD DATAFRAME AS result")

    result = dag.run("dask")
    return_df = result["result"].as_pandas()
    assert_eq(return_df, pd.DataFrame({"a": [1], "b": ["world"]}))

    result = dag.run(client)
    return_df = result["result"].as_pandas()
    assert_eq(return_df, pd.DataFrame({"a": [1], "b": ["world"]}))


def test_fugue_fsql(client):
    pdf = pd.DataFrame([[0, "hello"], [1, "world"]], columns=["a", "b"])
    dag = fugue_sql.fsql(
        "SELECT * FROM df WHERE a > 0 YIELD DATAFRAME AS result",
        df=pdf,
    )

    result = dag.run("dask")
    return_df = result["result"].as_pandas()
    assert_eq(return_df, pd.DataFrame({"a": [1], "b": ["world"]}))

    result = dag.run(client)
    return_df = result["result"].as_pandas()
    assert_eq(return_df, pd.DataFrame({"a": [1], "b": ["world"]}))


# TODO: uncomment if flaky failures persist on python 3.9
# @pytest.mark.flaky(reruns=4, condition="sys.version_info < (3, 9)")
def test_dask_fsql(client):
    def assert_fsql(df: pd.DataFrame) -> None:
        assert_eq(df, pd.DataFrame({"a": [1]}))

    # the simplest case: the SQL does not use any input and does not generate output
    fsql_dask(
        """
    CREATE [[0],[1]] SCHEMA a:long
    SELECT * WHERE a>0
    OUTPUT USING assert_fsql
    """
    )

    # it can directly use the dataframes inside dask-sql Context
    c = Context()
    c.create_table(
        "df", dd.from_pandas(pd.DataFrame([[0], [1]], columns=["a"]), npartitions=2)
    )

    fsql_dask(
        """
    SELECT * FROM df WHERE a>0
    OUTPUT USING assert_fsql
    """,
        c,
    )

    # for dataframes with name, they can register back to the Context (register=True)
    # the return of fsql is the dict of all dask dataframes with explicit names
    result = fsql_dask(
        """
    x=SELECT * FROM df WHERE a>0
    OUTPUT USING assert_fsql
    """,
        c,
        register=True,
    )
    assert isinstance(result["x"], dd.DataFrame)
    assert "x" in c.schema[c.schema_name].tables

    # integration test with fugue transformer extension
    c = Context()
    c.create_table(
        "df1",
        dd.from_pandas(
            pd.DataFrame([[0, 1], [1, 2]], columns=["a", "b"]), npartitions=2
        ),
    )
    c.create_table(
        "df2",
        dd.from_pandas(
            pd.DataFrame([[1, 2], [3, 4], [-4, 5]], columns=["a", "b"]), npartitions=2
        ),
    )

    # schema: *
    def cumsum(df: pd.DataFrame) -> pd.DataFrame:
        return df.cumsum()

    fsql_dask(
        """
    data = SELECT * FROM df1 WHERE a>0 UNION ALL SELECT * FROM df2 WHERE a>0 PERSIST
    result1 = TRANSFORM data PREPARTITION BY a PRESORT b USING cumsum
    result2 = TRANSFORM data PREPARTITION BY b PRESORT a USING cumsum
    PRINT result1, result2
    """,
        c,
        register=True,
    )
    assert "result1" in c.schema[c.schema_name].tables
    assert "result2" in c.schema[c.schema_name].tables
