from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime


def get_all_sessions(db: Session):
    sql = text("SELECT * FROM scraper_sessions")
    result = db.execute(sql).mappings().all()
    return list(result)


def start_new_session(db: Session):
    now = datetime.utcnow()
    sql = text(
        """
        INSERT INTO scraper_sessions (started_at, completion_status)
        VALUES (:started_at, :status)
        RETURNING session_id, started_at, ended_at, completion_status, error_log
    """
    )
    result = db.execute(sql, {"started_at": now, "status": "started"}).mappings()
    db.commit()
    return dict(result.fetchone())
