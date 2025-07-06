from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.module import ModuleCreate


def getAll(db: Session):
    sql = text("SELECT * FROM modules")
    result = db.execute(sql).mappings().all()
    return [dict(row) for row in result]


def getById(db: Session, moduleId: int):
    sql = text("SELECT * FROM modules WHERE module_id = :id")
    result = db.execute(sql, {"id": moduleId}).mappings().fetchone()
    return dict(result) if result else None


def create(db: Session, module: ModuleCreate):
    sql = text(
        """
        INSERT INTO modules (
            uc_id,
            module_name,
            teaching_period,
            semester,
            module_description,
            unit_code
        )
        VALUES (
            :uc_id,
            :module_name,
            :teaching_period,
            :semester,
            :module_description,
            :unit_code
        )
        RETURNING module_id, uc_id, module_name, teaching_period, semester, module_description, unit_code
    """
    )
    result = db.execute(
        sql,
        {
            "uc_id": module.uc_id,
            "module_name": module.module_name,
            "teaching_period": module.teaching_period,
            "semester": module.semester,
            "module_description": module.module_description,
            "unit_code": module.unit_code,
        },
    ).mappings()
    db.commit()
    return dict(result.fetchone())


def delete(db: Session, moduleId: int):
    sql = text(
        """
        DELETE FROM modules
        WHERE module_id = :id
        RETURNING module_id, uc_id, module_name, teaching_period, semester, module_description, unit_code
    """
    )
    result = db.execute(sql, {"id": moduleId}).mappings()
    db.commit()
    deleted = result.fetchone()
    return dict(deleted) if deleted else None
