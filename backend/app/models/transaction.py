import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import CorrectionStatus, ItemCondition, TransactionStatus


class Transaction(UUIDPKMixin, TimestampMixin, Base):
    """
    One record per item issued to a worker. Never deleted, only transitioned
    from ISSUED to RETURNED. Multiple items issued in one visit each get
    their own Transaction row (see product spec: no opaque combined records).
    """

    __tablename__ = "transactions"

    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workers.id"), nullable=False, index=True)
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("assets.id"), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        default=TransactionStatus.ISSUED,
        nullable=False,
        index=True,
    )

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    condition_on_return: Mapped[Optional[ItemCondition]] = mapped_column(
        Enum(ItemCondition, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=True,
    )
    condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    worker: Mapped["Worker"] = relationship()
    inventory_item: Mapped["InventoryItem"] = relationship()
    asset: Mapped[Optional["Asset"]] = relationship()

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_transaction_quantity_positive"),
        CheckConstraint(
            "(status = 'RETURNED' AND returned_at IS NOT NULL) OR "
            "(status = 'ISSUED' AND returned_at IS NULL)",
            name="ck_transaction_status_returned_at_consistency",
        ),
    )


class StockAdjustment(UUIDPKMixin, TimestampMixin, Base):
    """An audited manual change to a consumable item's stock levels."""

    __tablename__ = "stock_adjustments"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    adjusted_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)

    delta: Mapped[int] = mapped_column(Integer, nullable=False)  # can be negative
    previous_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class TransactionCorrection(UUIDPKMixin, TimestampMixin, Base):
    """
    Controlled correction mechanism for mistaken transactions. The original
    Transaction row and its audit trail are never edited or deleted; a
    correction request is layered on top and requires admin review.
    """

    __tablename__ = "transaction_corrections"

    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id"), nullable=False, index=True)
    requested_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[CorrectionStatus] = mapped_column(
        Enum(CorrectionStatus, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        default=CorrectionStatus.PENDING,
        nullable=False,
    )
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AuditLog(UUIDPKMixin, Base):
    """Append-only log of important actions. Ordinary users cannot edit/delete rows."""

    __tablename__ = "audit_logs"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
