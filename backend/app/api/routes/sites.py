import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.organization import Company, Department, Site
from app.models.user import User
from app.schemas.organization import (
    CompanyCreate,
    CompanyOut,
    DepartmentCreate,
    DepartmentOut,
    SiteCreate,
    SiteOut,
    SiteUpdate,
)
from app.services import audit_service

router = APIRouter(tags=["sites"])


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Company:
    company = Company(name=payload.name.strip())
    db.add(company)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A company with this name already exists.")
    audit_service.record(
        db, user_id=current_user.id, action="COMPANY_CREATED", entity_type="Company", entity_id=str(company.id)
    )
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[Company]:
    return list(db.execute(select(Company)).scalars().all())


@router.post("/sites", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Site:
    if db.get(Company, payload.company_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    site = Site(company_id=payload.company_id, name=payload.name.strip(), location=payload.location)
    db.add(site)
    db.flush()
    audit_service.record(
        db, user_id=current_user.id, action="SITE_CREATED", entity_type="Site", entity_id=str(site.id)
    )
    db.commit()
    db.refresh(site)
    return site


@router.get("/sites", response_model=list[SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.STOREKEEPER)),
) -> list[Site]:
    return list(db.execute(select(Site)).scalars().all())


@router.get("/sites/{site_id}", response_model=SiteOut)
def get_site(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.STOREKEEPER)),
) -> Site:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found.")
    return site


@router.patch("/sites/{site_id}", response_model=SiteOut)
def update_site(
    site_id: uuid.UUID,
    payload: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Site:
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(site, field, value)
    db.flush()
    audit_service.record(
        db, user_id=current_user.id, action="SITE_UPDATED", entity_type="Site", entity_id=str(site.id)
    )
    db.commit()
    db.refresh(site)
    return site


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Department:
    if db.get(Site, payload.site_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found.")
    dept = Department(site_id=payload.site_id, name=payload.name.strip())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.STOREKEEPER)),
) -> list[Department]:
    return list(db.execute(select(Department).where(Department.site_id == site_id)).scalars().all())
