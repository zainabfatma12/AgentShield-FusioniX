import sqlite3
from datetime import datetime, timezone


DATABASE_NAME = "agentshield.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()

    # --------------------------------------------------------
    # PROVIDERS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            reputation REAL NOT NULL,
            successful_transactions INTEGER NOT NULL DEFAULT 0,
            verified INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL,
            payment_protocol TEXT NOT NULL DEFAULT 'x402',
            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # TRANSACTIONS / AUDIT LEDGER
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            service TEXT NOT NULL,

            trust_score REAL NOT NULL,

            risk_level TEXT NOT NULL,

            decision TEXT NOT NULL,

            amount REAL NOT NULL,

            payment_protocol TEXT NOT NULL,

            authorized INTEGER NOT NULL,

            payment_status TEXT NOT NULL
                DEFAULT 'NOT_ATTEMPTED',

            blockchain TEXT,

            blockchain_tx_id TEXT,

            reason TEXT,

            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# PROVIDER OPERATIONS
# ============================================================

def save_provider(
    provider_id,
    name,
    description,
    reputation,
    successful_transactions,
    verified,
    price,
    payment_protocol="x402"
):

    connection = get_connection()

    now = datetime.now(timezone.utc).isoformat()

    connection.execute("""
        INSERT OR REPLACE INTO providers (
            provider_id,
            name,
            description,
            reputation,
            successful_transactions,
            verified,
            price,
            payment_protocol,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        provider_id,
        name,
        description,
        reputation,
        successful_transactions,
        int(verified),
        price,
        payment_protocol,
        now
    ))

    connection.commit()
    connection.close()


def get_providers():

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM providers
        ORDER BY id ASC
    """).fetchall()

    connection.close()

    providers = []

    for row in rows:

        provider = dict(row)

        provider["verified"] = bool(
            provider["verified"]
        )

        providers.append(provider)

    return providers


def get_provider(provider_id):

    connection = get_connection()

    row = connection.execute("""
        SELECT *
        FROM providers
        WHERE provider_id = ?
    """, (provider_id,)).fetchone()

    connection.close()

    if row is None:
        return None

    provider = dict(row)

    provider["verified"] = bool(
        provider["verified"]
    )

    return provider


# ============================================================
# TRANSACTION OPERATIONS
# ============================================================

def save_transaction(
    service,
    trust_score,
    risk_level,
    decision,
    amount,
    payment_protocol,
    authorized,
    reason,
    payment_status="NOT_ATTEMPTED",
    blockchain=None,
    blockchain_tx_id=None
):

    connection = get_connection()

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    cursor = connection.execute("""
        INSERT INTO transactions (
            service,
            trust_score,
            risk_level,
            decision,
            amount,
            payment_protocol,
            authorized,
            payment_status,
            blockchain,
            blockchain_tx_id,
            reason,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        service,
        trust_score,
        risk_level,
        decision,
        amount,
        payment_protocol,
        int(authorized),
        payment_status,
        blockchain,
        blockchain_tx_id,
        reason,
        timestamp
    ))

    connection.commit()

    transaction_id = cursor.lastrowid

    connection.close()

    return transaction_id


def update_payment_status(
    transaction_id,
    payment_status,
    blockchain=None,
    blockchain_tx_id=None
):

    connection = get_connection()

    connection.execute("""
        UPDATE transactions
        SET
            payment_status = ?,
            blockchain = ?,
            blockchain_tx_id = ?
        WHERE id = ?
    """, (
        payment_status,
        blockchain,
        blockchain_tx_id,
        transaction_id
    ))

    connection.commit()
    connection.close()


def get_transactions():

    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TRANSACTION STATISTICS
# ============================================================

def get_transaction_stats():

    connection = get_connection()

    total = connection.execute("""
        SELECT COUNT(*) AS count
        FROM transactions
    """).fetchone()["count"]

    approved = connection.execute("""
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE decision = 'APPROVE'
    """).fetchone()["count"]

    reviewed = connection.execute("""
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE decision = 'REVIEW'
    """).fetchone()["count"]

    blocked = connection.execute("""
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE decision = 'BLOCK'
    """).fetchone()["count"]

    connection.close()

    return {
        "total": total,
        "approved": approved,
        "reviewed": reviewed,
        "blocked": blocked
    }