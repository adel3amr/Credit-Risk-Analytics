from sqlalchemy import select, update
from . import schema as s
from .common import now, digest


def append(conn, actor, action, entity, details):
    # UPDATE obtains an exclusive row/write lock on both PostgreSQL and SQLite.
    conn.execute(
        update(s.audit_head)
        .where(s.audit_head.c.id == 1)
        .values(sequence=s.audit_head.c.sequence + 1)
    )
    head = (
        conn.execute(select(s.audit_head).where(s.audit_head.c.id == 1))
        .mappings()
        .one()
    )
    event = {
        "sequence": head["sequence"],
        "actor": actor,
        "action": action,
        "entity": entity,
        "recorded_at": now(),
        "details": details,
        "previous_hash": head["hash"],
    }
    event["hash"] = digest(event)
    conn.execute(s.audit_events.insert().values(**event))
    conn.execute(
        update(s.audit_head).where(s.audit_head.c.id == 1).values(hash=event["hash"])
    )


def verify(conn):
    previous = "GENESIS"
    count = 0
    for row in conn.execute(
        select(s.audit_events).order_by(s.audit_events.c.sequence)
    ).mappings():
        row = dict(row)
        recorded = row.pop("hash")
        count += 1
        if (
            row["sequence"] != count
            or row["previous_hash"] != previous
            or digest(row) != recorded
        ):
            raise ValueError("Audit chain mismatch")
        previous = recorded
    head = conn.execute(select(s.audit_head)).mappings().one()
    if head["hash"] != previous or head["sequence"] != count:
        raise ValueError("Audit head mismatch")
    return {"events": count, "head": previous, "status": "VERIFIED"}
