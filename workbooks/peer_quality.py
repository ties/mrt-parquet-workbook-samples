# /// script
# dependencies = [
#     "duckdb==1.4.4",
#     "marimo",
#     "polars==1.38.1",
#     "pyarrow==23.0.1",
#     "sqlglot==28.10.1",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.19.11"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # RIB dump (bview) and update consistency

    After an [infrastructure issue](https://status.ripe.net/incidents/b37pjbr41jyy) we wanted to double check that the bview files are consistent. This means that they only contain routes for peers that have a real BGP session with RIS.

    For this analysis we consider a BGP session to be alive when non-state change messages are present in the MRT files.

    We use three types of files:

    * All BGP updates for 24h
    * All bview files for 00:00:00 following those updates
    * The total number of BGP messages (per peer ip $\times$ peer asn, per type - state change, update, notification, ...) for each update file.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import duckdb

    import os

    return duckdb, mo, os


@app.cell
def _(duckdb, os):
    conn = duckdb.connect()

    PEER_MESSAGE_COUNT = os.path.expanduser(
        "~/src/tmp/parquet/peer_message_count-2026-02-16.parquet"
    )
    PEER_STATUS = os.path.expanduser("~/src/tmp/parquet/peer_status-2026-02-16.parquet")

    UPDATES = os.path.expanduser("~/src/tmp/parquet/updates/**/*.parquet")
    BVIEW = os.path.expanduser("~/src/tmp/parquet/bview/**/*.parquet")

    conn.query(f"ATTACH '{PEER_MESSAGE_COUNT}' as peer_message_count")
    conn.query(f"ATTACH '{PEER_STATUS}' as peer_status")
    conn.query(f"CREATE VIEW updates AS (SELECT * FROM '{UPDATES}')")
    conn.query(f"CREATE VIEW bview AS (SELECT * FROM '{BVIEW}')")
    return (conn,)


@app.cell
def _(conn):
    conn.query("SELECT count(*), peer_ip, peer_asn from updates group by all").pl()
    return


@app.cell
def _(conn):
    conn.query("""
    CREATE TEMPORARY TABLE peer_messages AS (
    SELECT
        peer_ip,
        peer_asn,
        sum(msg_bytes) msg_bytes,
        sum(num_state_change) num_state_change,
        sum(num_open) num_open,
        sum(num_update) num_update,
        sum(num_update_announced) num_update_announced,
        sum(num_update_withdrawn) num_update_withdrawn,
        sum(num_notification) num_notification,
        sum(num_keepalive) num_keepalive,
        sum(total_messages) total_messages
    FROM peer_message_count.peer_message_count
    GROUP BY ALL
    )
    """)
    return


@app.cell(hide_code=True)
def _(conn, mo, peer_messages):
    _df = mo.sql(
        """
        --- Integrity check
        SELECT * FROM peer_messages WHERE num_state_change + num_open + num_update + num_notification + num_keepalive != total_messages;
        """,
        engine=conn,
    )
    return


@app.cell(hide_code=True)
def _(bview, conn, mo, peer_messages):
    _df = mo.sql(
        """
        --- Get the peers that have only sent status change messages during 24h
        ---
        --- or less than 24 messages total (we expect one notification every 5m by default)
        WITH peer_cnt AS (
            SELECT count(*) cnt, peer_ip, peer_asn FROM bview GROUP BY ALL
        )
        SELECT * FROM peer_cnt pc LEFT JOIN peer_messages pm ON pc.peer_ip = pm.peer_ip AND pc.peer_asn = pm.peer_asn
        WHERE total_messages - num_state_change = 0 OR total_messages - num_state_change < 24
        """,
        engine=conn,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **No result**.

    This means that all peers that have routes in the bview, are actively sending BGP messages.
    """)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
