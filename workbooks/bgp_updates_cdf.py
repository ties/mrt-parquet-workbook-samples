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
    import duckdb

    return (duckdb,)


@app.cell
def _(conn):
    conn.query("DESCRIBE 'data/bview/**/*.parquet'")
    return


@app.cell
def _(duckdb):
    # Use an explicit session, to prevent an issue I experienced where duckdb would only
    # execute the query on one core in a Marimo notebook.
    conn = duckdb.connect()

    conn.query("""
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
        (7018);
    """)

    return (conn,)


@app.cell
def _(conn):
    conn.query("""
    WITH prefixes_transiting AS (
    SELECT
        DISTINCT prefix,
        CASE WHEN ':' in prefix THEN 'ipv6' ELSE 'ipv4' END AS afi,
        asn
    FROM tier_one
    LEFT JOIN 'data/bview/**/*.parquet' ris
    ON asn IN ris.as_path
    )
    SELECT count(*), asn, afi from prefixes_transiting GROUP BY ALL
    """)
    return


@app.cell
def _(conn):
    conn.query("""
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
        (7018);


    WITH path_tier_ones AS (
        -- For each route, find all tier-one ASNs in its path
        SELECT
            b.*,
            array_agg(DISTINCT t.asn) AS tier_one_asns,
            COUNT(DISTINCT t.asn) AS tier_one_count
        FROM
            'data/bview/**/*.parquet' b,
            UNNEST(b.as_path) AS path_asn
        LEFT JOIN
            tier_one t ON t.asn = path_asn
        WHERE
            t.asn IS NOT NULL
        GROUP BY ALL
    )
    SELECT
        ts,
        prefix,
        origin_as,
        as_path,
        peer_asn,
        tier_one_asns AS tier_ones_in_path,
        tier_one_count
    FROM
        path_tier_ones
    WHERE
        tier_one_count = 2
    ORDER BY
        ts DESC, prefix;
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
