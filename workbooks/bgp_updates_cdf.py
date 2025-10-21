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
    return duckdb, mo, plt


@app.cell
def _(duckdb):
    # Use an explicit session, to prevent an issue I experienced where duckdb would only
    # execute the query on one core in a Marimo notebook.
    conn = duckdb.connect()

    conn.query(f"""
    CREATE TEMPORARY TABLE freqs AS
        SELECT count(*) update_count, operation, prefix, origin_as, year, month
        FROM './data/updates/**/*.parquet'
        GROUP BY ALL;
    """)
    return (conn,)


@app.cell
def _(conn, mo):
    mo.output.append(conn.sql("DESCRIBE freqs"))

    df = conn.sql("""
    SELECT
    update_count, prefix, operation, origin_as,
    SUM (update_count) OVER (ORDER BY update_count) AS cumulative_sum,
    SUM (update_count) OVER (ORDER BY update_count) / SUM (update_count) OVER () AS cdf
    FROM freqs
    ORDER BY 1 DESC
    """).df ()
    df[0:3]
    return (df,)


@app.cell
def _(df, plt):
    plt.figure(figsize=(10, 6), dpi=100)

    # Filter data by operation type
    df_a = df[df['operation'] == 'A']
    df_w = df[df['operation'] == 'W']

    # Plot both lines with ColorBrewer colours
    plt.step(df_a['update_count'], df_a['cdf'], where='post', 
             linestyle='-', color='#1f77b4', label='A')
    plt.step(df_w['update_count'], df_w['cdf'], where='post', 
             linestyle='-', color='#ff7f0e', label='W')

    plt.xlabel('Update Count')
    plt.ylabel('CDF')
    plt.title('Number of BP updates seen (RIPE RIS, 2025-10-10) per prefix (CDF)')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
