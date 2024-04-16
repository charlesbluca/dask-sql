import dask
import pytest

pytest_plugins = ["tests.integration.fixtures"]


def pytest_addoption(parser):
    parser.addoption("--rungpu", action="store_true", help="run tests meant for GPU")
    parser.addoption("--runqueries", action="store_true", help="run test queries")
    parser.addoption("--data_dir", help="specify file path to the data")
    parser.addoption("--queries_dir", help="specify file path to the queries")


def pytest_runtest_setup(item):
    # TODO: get pyarrow strings and p2p shuffle working
    dask.config.set({"dataframe.convert-string": False})
    dask.config.set({"dataframe.shuffle.method": "tasks"})
    if "gpu" in item.keywords:
        if not item.config.getoption("--rungpu"):
            pytest.skip("need --rungpu option to run")
        # manually enable cudf decimal support
        dask.config.set({"sql.mappings.decimal_support": "cudf"})
    if "queries" in item.keywords and not item.config.getoption("--runqueries"):
        pytest.skip("need --runqueries option to run")


@pytest.fixture(scope="session")
def data_dir(request):
    return request.config.getoption("--data_dir")


@pytest.fixture(scope="session")
def queries_dir(request):
    return request.config.getoption("--queries_dir")
