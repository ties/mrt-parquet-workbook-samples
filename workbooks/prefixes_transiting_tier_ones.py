# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "duckdb==1.4.1",
#     "matplotlib==3.10.7",
#     "pandas==2.3.3",
#     "polars==1.34.0",
#     "pyarrow==21.0.0",
#     "sqlglot==27.27.0",
# ]
# ///

import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import duckdb

    import polars as pl
    import matplotlib.pyplot as plt
    return (duckdb,)


@app.cell
def _(duckdb):
    duckdb.sql("""
    CREATE TEMPORARY TABLE tier_one (asn VARCHAR);
    INSERT INTO tier_one VALUES
        (701),
        (174),
        (12956),
        (6939),
        (3257),
        (6461),
        (6762),
        (6453),
        (1299),
        (6830),
        (2914),
        (3491),
        (5511),
        (3356),
        (3320),
        (7922), --- Comast
        (4134), --- Chinanet
        (7018);
    """)
    return (tier_one,)


@app.cell
def _(duckdb, tier_one):
    duckdb.sql("""
    CREATE TEMPORARY TABLE tier_one_transiting AS (
        SELECT
            DISTINCT prefix,
            CASE WHEN ':' in prefix THEN 'ipv6' ELSE 'ipv4' END AS afi,
            asn,
        FROM tier_one
        LEFT JOIN 'data/bview/**/*.parquet' ris
        ON asn IN ris.as_path
    );
    """)
    return


@app.cell
def _(duckdb):
    duckdb.sql("""
    PIVOT (SELECT * FROM tier_one_transiting)
    ON afi USING count(distinct prefix) ORDER BY asn::int ASC
    """).df()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
