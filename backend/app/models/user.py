import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import UserRole


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("companies.id"), nullable=True, index=True
    )
    # A storekeeper/manager is normally scoped to one site. Admins may be
    # company-wide (site_id NULL) or site-scoped.
    site_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("sites.id"), nullable=True, index=True
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped[Optional["Company"]] = relationship(back_populates="users")
