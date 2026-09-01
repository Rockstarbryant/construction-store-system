"""
Seeds development data: a demo company/site, an admin/storekeeper/manager
user, a handful of workers, and a starter inventory.

Run with: ./venv/bin/python -m app.db.seed
Uses obviously fake data only - never real people's National IDs or phone
numbers.
"""
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import ItemType, UserRole
from app.models.inventory import InventoryItem
from app.models.organization import Company, Site
from app.models.user import User
from app.schemas.worker import WorkerCreate
from app.services.worker_service import register_worker


def run() -> None:
    db = SessionLocal()
    try:
        company = db.query(Company).filter(Company.name == "Demo Construction Ltd").one_or_none()
        if company is None:
            company = Company(name="Demo Construction Ltd")
            db.add(company)
            db.flush()

        site = db.query(Site).filter(Site.name == "Westlands Construction Site").one_or_none()
        if site is None:
            site = Site(company_id=company.id, name="Westlands Construction Site", location="Nairobi")
            db.add(site)
            db.flush()

        seed_users = [
            ("admin@demo-construction.example.com", "AdminPass123!", "Alice Admin", UserRole.ADMIN),
            ("storekeeper@demo-construction.example.com", "StorePass123!", "Sam Storekeeper", UserRole.STOREKEEPER),
            ("manager@demo-construction.example.com", "ManagerPass123!", "Mary Manager", UserRole.MANAGER),
        ]
        for email, password, name, role in seed_users:
            if db.query(User).filter(User.email == email).one_or_none() is None:
                db.add(
                    User(
                        email=email,
                        hashed_password=hash_password(password),
                        full_name=name,
                        role=role,
                        company_id=company.id,
                        site_id=site.id,
                    )
                )
        db.flush()

        seed_workers = [
            ("John Kamau", "10000001", "0712000001"),
            ("Peter Otieno", "10000002", "0712000002"),
            ("Brian Mwangi", "10000003", "0712000003"),
        ]
        for full_name, national_id, phone in seed_workers:
            already = (
                db.query(User)  # placeholder no-op check pattern avoided; real check below
            )
            from app.models.worker import Worker

            exists = db.query(Worker).filter(
                Worker.site_id == site.id, Worker.national_id == national_id
            ).one_or_none()
            if exists is None:
                register_worker(
                    db,
                    WorkerCreate(
                        site_id=site.id,
                        full_name=full_name,
                        national_id=national_id,
                        phone_number=phone,
                    ),
                )

        seed_items = [
            ("Spade", "Hand Tools", ItemType.CONSUMABLE, 20),
            ("Bucket", "Hand Tools", ItemType.CONSUMABLE, 30),
            ("Hammer", "Hand Tools", ItemType.CONSUMABLE, 15),
            ("Safety Belt", "PPE", ItemType.CONSUMABLE, 25),
            ("Helmet", "PPE", ItemType.CONSUMABLE, 40),
            ("Reflective Vest", "PPE", ItemType.CONSUMABLE, 40),
            ("Cutting Machine", "Power Equipment", ItemType.ASSET, 0),
            ("Drill", "Power Equipment", ItemType.ASSET, 0),
        ]
        for name, category, item_type, qty in seed_items:
            exists = db.query(InventoryItem).filter(
                InventoryItem.site_id == site.id, InventoryItem.name == name
            ).one_or_none()
            if exists is None:
                db.add(
                    InventoryItem(
                        site_id=site.id,
                        name=name,
                        category=category,
                        item_type=item_type,
                        total_quantity=qty,
                        available_quantity=qty,
                        issued_quantity=0,
                    )
                )
        db.flush()

        db.commit()
        print("Seed complete.")
        print(f"Company: {company.name} ({company.id})")
        print(f"Site: {site.name} ({site.id})")
        print("Users:")
        for email, password, name, role in seed_users:
            print(f"  {role.value}: {email} / {password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
