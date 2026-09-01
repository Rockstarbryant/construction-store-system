import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class Company(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sites: Mapped[List["Site"]] = relationship(back_populates="company")
    users: Mapped[List["User"]] = relationship(back_populates="company")


class Site(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sites"

    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="sites")
    departments: Mapped[List["Department"]] = relationship(back_populates="site")
    workers: Mapped[List["Worker"]] = relationship(back_populates="site")
    inventory_items: Mapped[List["InventoryItem"]] = relationship(back_populates="site")

    __table_args__ = ()


class Department(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    site: Mapped["Site"] = relationship(back_populates="departments")
