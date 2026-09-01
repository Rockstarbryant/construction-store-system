export type UserRole = "ADMIN" | "STOREKEEPER" | "MANAGER";

export type WorkerStatus = "ACTIVE" | "INACTIVE";

export type ItemType = "CONSUMABLE" | "ASSET";

export type InventoryItemStatus = "ACTIVE" | "DISABLED";

export type TransactionStatus = "ISSUED" | "RETURNED";

export type ItemCondition = "GOOD" | "FAIR" | "DAMAGED" | "NEEDS_REPAIR" | "LOST";

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  company_id: string | null;
  site_id: string | null;
}

export interface Company {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

export interface Site {
  id: string;
  company_id: string;
  name: string;
  location: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Department {
  id: string;
  site_id: string;
  name: string;
}

export interface Worker {
  id: string;
  site_id: string;
  store_number: string;
  full_name: string;
  national_id_masked: string;
  phone_number: string;
  department_id: string | null;
  job_role: string | null;
  supervisor: string | null;
  employment_status: string | null;
  status: WorkerStatus;
  created_at: string;
}

export interface WorkerSearchResult {
  id: string;
  store_number: string;
  full_name: string;
  phone_number: string;
  status: WorkerStatus;
}

export interface InventoryItem {
  id: string;
  site_id: string;
  name: string;
  category: string | null;
  item_type: ItemType;
  total_quantity: number;
  available_quantity: number;
  issued_quantity: number;
  status: InventoryItemStatus;
  created_at: string;
}

export interface StockAdjustment {
  id: string;
  inventory_item_id: string;
  delta: number;
  previous_quantity: number;
  new_quantity: number;
  reason: string;
  created_at: string;
}

export interface TransactionOut {
  id: string;
  site_id: string;
  worker_id: string;
  worker_full_name: string;
  worker_store_number: string;
  inventory_item_id: string;
  inventory_item_name: string;
  asset_id: string | null;
  quantity: number;
  status: TransactionStatus;
  issued_at: string;
  returned_at: string | null;
  condition_on_return: ItemCondition | null;
  condition_notes: string | null;
}

export interface DashboardStats {
  total_workers: number;
  active_workers: number;
  total_inventory_items: number;
  items_currently_issued: number;
  items_issued_today: number;
  items_returned_today: number;
  damaged_items: number;
  recent_activity: {
    worker: string;
    store_number: string | null;
    item: string;
    action: "took" | "returned";
    timestamp: string;
  }[];
}

export interface DailyReport {
  date: string;
  workers_served: number;
  items_issued: number;
  items_returned: number;
  currently_outstanding: number;
}

export interface InventoryReportLine {
  item: string;
  total: number;
  available: number;
  issued: number;
  damaged: number;
}

export interface AuditLogEntry {
  id: string;
  created_at: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  metadata: string | null;
}

export interface ApiErrorBody {
  detail?: string;
  errors?: { loc: (string | number)[]; msg: string }[];
}
