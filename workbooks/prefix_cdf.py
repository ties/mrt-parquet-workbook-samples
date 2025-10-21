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
def _():
    return


if __name__ == "__main__":
    app.run()
