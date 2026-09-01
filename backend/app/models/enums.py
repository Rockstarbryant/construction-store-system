import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STOREKEEPER = "STOREKEEPER"
    MANAGER = "MANAGER"


class WorkerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ItemType(str, enum.Enum):
    CONSUMABLE = "CONSUMABLE"  # quantity-based (gloves, cement bags, masks...)
    ASSET = "ASSET"  # individually tracked (cutting machines, generators...)


class InventoryItemStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class AssetStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ISSUED = "ISSUED"
    DAMAGED = "DAMAGED"
    NEEDS_REPAIR = "NEEDS_REPAIR"
    LOST = "LOST"
    RETIRED = "RETIRED"


class TransactionStatus(str, enum.Enum):
    ISSUED = "ISSUED"
    RETURNED = "RETURNED"


class ItemCondition(str, enum.Enum):
    GOOD = "GOOD"
    FAIR = "FAIR"
    DAMAGED = "DAMAGED"
    NEEDS_REPAIR = "NEEDS_REPAIR"
    LOST = "LOST"


class CorrectionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
