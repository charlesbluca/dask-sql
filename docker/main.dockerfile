# Dockerfile for dask-sql running the SQL server
# For more information, see https://dask-sql.readthedocs.io/.
FROM daskdev/dask:latest
LABEL author "Nils Braun <nilslennartbraun@gmail.com>"

# Install dependencies for dask-sql
COPY docker/conda.txt /opt/dask_sql/
RUN conda config --add channels conda-forge \
    && /opt/conda/bin/conda install --freeze-installed \
    "tzlocal>=2.1" \
    "fastapi>=0.69.0" \
    "uvicorn>=0.11.3" \
    "pyarrow>=6.0.1" \
    "prompt_toolkit>=3.0.8" \
    "pygments>=2.7.1" \
    "dask-ml>=2022.1.22" \
    "setuptools-rust>=1.4.1" \
    "scikit-learn>=1.0.0" \
    "intake>=0.6.0" \
    && conda clean -ay

# install dask-sql
COPY setup.py /opt/dask_sql/
COPY setup.cfg /opt/dask_sql/
COPY versioneer.py /opt/dask_sql/
COPY .git /opt/dask_sql/.git
COPY dask_planner /opt/dask_sql/dask_planner
COPY dask_sql /opt/dask_sql/dask_sql
RUN cd /opt/dask_sql/ \
    && pip install -e .

# Set the script to execute
COPY scripts/startup_script.py /opt/dask_sql/startup_script.py

EXPOSE 8080
ENTRYPOINT [ "/usr/bin/prepare.sh", "/opt/conda/bin/python", "/opt/dask_sql/startup_script.py" ]
