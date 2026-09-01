import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import WorkerStatus
from app.models.worker import Worker, WorkerStoreNumberSequence
from app.schemas.worker import WorkerCreate, WorkerUpdate
from app.utils.formatting import next_store_number


def _allocate_store_number(db: Session, site_id: uuid.UUID) -> str:
    """
    Atomically allocates the next store number for a site.

    Uses SELECT ... FOR UPDATE to lock the site's sequence row for the
    duration of the enclosing transaction, so concurrent registrations at
    the same site are serialized and can never collide. The row is created
    (locked at INSERT time) on first use for a site.
    """
    seq = db.execute(
        select(WorkerStoreNumberSequence)
        .where(WorkerStoreNumberSequence.site_id == site_id)
        .with_for_update()
    ).scalar_one_or_none()

    if seq is None:
        # First worker at this site. Two concurrent requests may both see no
        # row and both try to create one; the unique constraint on site_id
        # lets only one INSERT win. Use a SAVEPOINT so a losing insert can be
        # rolled back without aborting the caller's outer transaction, then
        # re-select-for-update against the row the winner created.
        nested = db.begin_nested()
        try:
            seq = WorkerStoreNumberSequence(site_id=site_id, last_number=0)
            db.add(seq)
            db.flush()
            nested.commit()
        except IntegrityError:
            nested.rollback()
            seq = db.execute(
                select(WorkerStoreNumberSequence)
                .where(WorkerStoreNumberSequence.site_id == site_id)
                .with_for_update()
            ).scalar_one()

    new_number, padded = next_store_number(seq.last_number)
    seq.last_number = new_number
    db.flush()
    return padded


def register_worker(db: Session, payload: WorkerCreate) -> Worker:
    # Re-activation path: if a worker with this National ID already exists
    # at this site (even if INACTIVE), reuse their existing store number
    # rather than issuing a new one.
    existing = db.execute(
        select(Worker).where(
            Worker.site_id == payload.site_id,
            Worker.national_id == payload.national_id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        if existing.status == WorkerStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Worker with National ID {payload.national_id} already exists "
                f"(Store Number {existing.store_number}).",
            )
        # Reactivate instead of creating a duplicate / new number.
        existing.status = WorkerStatus.ACTIVE
        existing.full_name = payload.full_name
        existing.phone_number = payload.phone_number
        existing.department_id = payload.department_id
        existing.job_role = payload.job_role
        existing.supervisor = payload.supervisor
        existing.employment_status = payload.employment_status
        db.flush()
        return existing

    try:
        store_number = _allocate_store_number(db, payload.site_id)
        worker = Worker(
            site_id=payload.site_id,
            store_number=store_number,
            full_name=payload.full_name,
            national_id=payload.national_id,
            phone_number=payload.phone_number,
            department_id=payload.department_id,
            job_role=payload.job_role,
            supervisor=payload.supervisor,
            employment_status=payload.employment_status,
            status=WorkerStatus.ACTIVE,
        )
        db.add(worker)
        db.flush()
        return worker
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not register worker due to a conflicting record. Please retry.",
        ) from exc


def search_workers(db: Session, site_id: uuid.UUID, query: str, limit: int = 20) -> list[Worker]:
    query = query.strip()
    if not query:
        return []
    like = f"%{query}%"
    stmt = (
        select(Worker)
        .where(
            Worker.site_id == site_id,
            or_(
                Worker.store_number.ilike(like),
                Worker.full_name.ilike(like),
                Worker.national_id.ilike(like),
                Worker.phone_number.ilike(like),
            ),
        )
        .order_by(Worker.full_name)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_worker(db: Session, worker_id: uuid.UUID) -> Worker:
    worker = db.get(Worker, worker_id)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found.")
    return worker


def update_worker(db: Session, worker_id: uuid.UUID, payload: WorkerUpdate) -> Worker:
    worker = get_worker(db, worker_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)
    db.flush()
    return worker
