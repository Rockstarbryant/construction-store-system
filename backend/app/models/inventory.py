import uuid
from typing import List, Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import AssetStatus, InventoryItemStatus, ItemType


class InventoryItem(UUIDPKMixin, TimestampMixin, Base):
    """
    A type of item stocked at a site (e.g. "Safety Belt", "Cutting Machine").

    For CONSUMABLE items, quantities on this row are the source of truth.
    For ASSET items, this row represents the item *type*; each physical unit
    is a row in `assets`, and total/available/issued here are kept in sync
    as a fast-path summary for listing/reporting.
    """

    __tablename__ = "inventory_items"

    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )

    total_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issued_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[InventoryItemStatus] = mapped_column(
        Enum(InventoryItemStatus, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        default=InventoryItemStatus.ACTIVE,
        nullable=False,
    )

    site: Mapped["Site"] = relationship(back_populates="inventory_items")
    assets: Mapped[List["Asset"]] = relationship(back_populates="inventory_item")

    __table_args__ = (
        UniqueConstraint("site_id", "name", name="uq_inventory_item_site_name"),
        CheckConstraint("total_quantity >= 0", name="ck_inventory_total_nonneg"),
        CheckConstraint("available_quantity >= 0", name="ck_inventory_available_nonneg"),
        CheckConstraint("issued_quantity >= 0", name="ck_inventory_issued_nonneg"),
    )


class Asset(UUIDPKMixin, TimestampMixin, Base):
    """An individually tracked physical unit of an ASSET-type inventory item."""

    __tablename__ = "assets"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id"), nullable=False, index=True
    )
    asset_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, native_enum=False, values_callable=lambda e: [x.value for x in e]),
        default=AssetStatus.AVAILABLE,
        nullable=False,
    )

    inventory_item: Mapped["InventoryItem"] = relationship(back_populates="assets")
