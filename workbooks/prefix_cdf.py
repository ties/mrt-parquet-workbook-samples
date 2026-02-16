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

__generated_with = "0.17.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import duckdb

    import polars as pl
    import matplotlib.pyplot as plt
    return duckdb, pl, plt


@app.cell
def _(duckdb):
    df = duckdb.query(f"""
        CREATE OR REPLACE MACRO proto(addr) AS CASE WHEN ':' IN addr THEN 'v6' ELSE 'v4' END;

        SELECT
            count(*) cnt,
            proto(prefix) proto,
            peer_ip,
            peer_asn
        FROM './data/20251010.0000-ris-all-collectors.parquet'
        GROUP BY
            ALL;
        """).pl()
    return (df,)


@app.cell
def _(df, pl, plt):
    # https://claude.ai/share/2d35f098-96f9-4841-a5f8-227118a1be5d
    # Group by peer (peer_ip + peer_asn) and proto to get count of prefixes per peer
    peer_counts = (
        df.group_by(['peer_ip', 'peer_asn', 'proto'])
        .agg(pl.col('cnt').sum().alias('prefix_count'))
    )

    # Create the CDF plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get unique protocol values
    protocols = peer_counts['proto'].unique().to_list()

    for proto in protocols:
        # Filter data for this protocol and sort
        proto_data = (
            peer_counts
            .filter(pl.col('proto') == proto)
            .select('prefix_count')
            .sort('prefix_count')
            .to_series()
            .to_list()
        )

        # Calculate CDF values
        n = len(proto_data)
        cdf = [i / n for i in range(1, n + 1)]

        # Plot
        ax.plot(proto_data, cdf, label=f'Protocol: {proto}', linewidth=2)

    ax.set_xlabel('Number of Prefixes', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('CDF of Prefix Count per RIS Peer', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(duckdb):
    df_1min = duckdb.query("select count(*) num_updates, time_bucket(interval '5 minutes', ts) time_window from '~/src/tmp/parquet/updates/**/*.parquet' where day='26' group by all order by time_window asc;").df()
    return (df_1min,)


@app.cell
def _(df_1min, plt):
    # import matplotlib.pyplot as plt
    # import pandas as pd

    plt.figure(figsize=(10, 6))
    plt.bar(df_1min['time_window'], df_1min['num_updates'], width=0.0007)
    plt.xlabel('Time Window')
    plt.ylabel('Number of Updates')
    plt.title('Number of Updates Over Time')
    plt.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(duckdb):
    df_cdf = duckdb.query("""
    WITH base_counts AS (
      SELECT 
        count(*) as num_updates, 
        prefix 
      FROM '~/src/tmp/parquet/updates/**/*.parquet' 
      WHERE day='26' 
      GROUP BY ALL 
      ORDER BY num_updates DESC
    ),
    with_cumulative AS (
      SELECT
        prefix,
        num_updates,
        SUM(num_updates) OVER (ORDER BY num_updates DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_updates,
        SUM(num_updates) OVER () as total_updates
      FROM base_counts
    )
    SELECT
      prefix,
      num_updates,
      cumulative_updates::FLOAT / total_updates as cdf,
    FROM with_cumulative
    ORDER BY num_updates DESC;
    """).df()
    return (df_cdf,)


@app.cell
def _(df_cdf):
    df_cdf
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
