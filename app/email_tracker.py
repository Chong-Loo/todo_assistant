from datetime import datetime

from app.db import get_connection


def record_fetched_emails(emails, username: str, mailbox: str = "INBOX"):
    if not emails:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        rows = []
        for mail in emails:
            uid = mail.get("uid")
            if uid is None:
                continue
            rows.append((
                int(uid),
                str(mail.get("message_id", "") or ""),
                str(mail.get("subject", "") or ""),
                str(mail.get("from", "") or ""),
                str(mail.get("date", "") or ""),
                now,
                mailbox,
                username,
            ))

        if not rows:
            return

        conn.executemany(
            """
            INSERT OR IGNORE INTO processed_emails
                (uid, message_id, subject, from_addr, date, fetched_at, mailbox, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()


def get_fetched_uids(username: str, mailbox: str = "INBOX") -> set[int]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT uid FROM processed_emails
            WHERE username = ? AND mailbox = ?
            """,
            (username, mailbox),
        ).fetchall()
        return {int(row["uid"]) for row in rows}


def clear_tracking(username: str | None = None):
    with get_connection() as conn:
        if username:
            conn.execute(
                "DELETE FROM processed_emails WHERE username = ?",
                (username,),
            )
        else:
            conn.execute("DELETE FROM processed_emails")
        conn.commit()
