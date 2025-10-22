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
    # Use an explicit session, to prevent an issue I experienced where duckdb would only
    # execute the query on one core in a Marimo notebook.
    conn = duckdb.connect()

    # Macro that checks an AS-path for a peerlock violation
    # comcast and chinanet are added here as tier1s.
    # Telstra/4637 is not added because it is regional (and likely is the final tier1 in the AS, making it effectively a upstream)
    conn.query("""
    CREATE OR REPLACE MACRO has_non_consecutive_tier_ones (
        as_path
    )
    AS (
        WITH tier_one_positions AS (
        SELECT
            list_filter (RANGE (1,
            len (as_path) + 1),
            idx -> as_path[idx] IN ('701', '174', '12956', '6939', '3257', '6461', '6762', '6453', '1299', '6830', '2914', '3491', '5511', '3356', '3320', '7018', '7922', '4134')
    ) AS positions
    )
            SELECT
                len (positions) >= 2
                AND (list_max (positions) - list_min (positions) + 1) > len (positions)
            FROM
                tier_one_positions
    );
    """)
    return (conn,)


@app.cell
def _(conn):
    conn.query("DROP TABLE IF EXISTS peerlock_violations")
    conn.query("""
    CREATE TEMPORARY TABLE peerlock_violations AS (
        SELECT prefix, as_path
        FROM 'data/bview/**/*.parquet'
        WHERE has_non_consecutive_tier_ones(as_path)
    );
    """)

    df = conn.query("SELECT * FROM peerlock_violations").df()
    df
    return


@app.cell
def _(conn):
    conn.query("SELECT count(*), as_path FROM peerlock_violations GROUP BY ALL ORDER BY 1 DESC").df()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
