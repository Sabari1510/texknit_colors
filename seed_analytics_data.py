import datetime
import random
from database.models import (
    initialize_db, db, User, Supplier, Material, Transaction, MRS, MRSItem,
    ProductInward, PIItem, Invoice, Consumer, CompanyProfile
)

def seed_data():
    print("Connecting to database...")
    initialize_db()
    db.connect(reuse_if_open=True)

    # 1. Clear existing invoice data
    print("Deleting existing Invoices, MRSItems, and MRS records...")
    Invoice.delete().execute()
    MRSItem.delete().execute()
    MRS.delete().execute()

    # Set a default late fee in the profile for testing
    profile = CompanyProfile.get_or_none()
    if profile:
        profile.daily_late_fee = 50.0  # ₹50 per day late fee
        profile.save()

    # 2. Ensure we have an admin user and consumers
    admin = User.get(User.username == 'admin')
    consumers = list(Consumer.select())
    if not consumers:
        print("No consumers found. Seeding basic consumers...")
        consumer_names = ["Global Textiles Ltd", "Skyline Apparels", "Oceanic Prints", "Urban Fabrics", "Heritage Knits"]
        for name in consumer_names:
            c = Consumer.create(
                company_name=name,
                contact_person=f"{name.split()[0]} Manager",
                phone=f"98765{random.randint(10000, 99999)}",
                gst_no=f"33AAAAA{random.randint(1000, 9999)}A1Z5",
                location="Tirupur"
            )
            consumers.append(c)

    materials = list(Material.select())
    today = datetime.date.today()

    print("Generating new Detailed Invoices...")
    
    # Scenarios to seed:
    # 1. PAID (Recent)
    # 2. SENT (Within due date)
    # 3. DRAFT (Recent)
    # 4. OVERDUE (Past due date)

    scenarios = [
        {'status': 'PAID', 'created_offset': 10, 'due_offset': 5, 'count': 3},
        {'status': 'SENT', 'created_offset': 5, 'due_offset': 7, 'count': 4},
        {'status': 'DRAFT', 'created_offset': 2, 'due_offset': 14, 'count': 3},
        {'status': 'SENT', 'created_offset': 45, 'due_offset': -15, 'count': 5}, # Overdue
    ]

    invoice_count = 0
    for s in scenarios:
        for _ in range(s['count']):
            invoice_count += 1
            consumer = random.choice(consumers)
            
            # Create MRS first
            mrs = MRS.create(
                batch_id=f"B-{2026}-{invoice_count:03d}",
                supervisor=admin,
                status='ISSUED' if s['status'] != 'DRAFT' else 'PENDING',
                created_at=datetime.datetime.now() - datetime.timedelta(days=s['created_offset'] + random.randint(0, 5))
            )
            
            # Add MRS items
            total_amount = 0
            for _ in range(random.randint(1, 3)):
                mat = random.choice(materials)
                qty = random.uniform(10, 50)
                MRSItem.create(
                    mrs=mrs,
                    material=mat,
                    quantity_requested=qty,
                    quantity_issued=qty if s['status'] != 'DRAFT' else 0
                )
                total_amount += qty * mat.unit_cost

            # Compute taxes
            tax = total_amount * 0.18
            grand_total = total_amount + tax
            
            # Create Invoice
            is_overdue = s['status'] == 'SENT' and s['due_offset'] < 0
            
            Invoice.create(
                invoice_no=f"INV-26-{invoice_count:03d}",
                mrs=mrs,
                total_amount=total_amount,
                tax_amount=tax,
                grand_total=grand_total,
                client_name=consumer.company_name,
                client_address=consumer.location,
                client_gstin=consumer.gst_no,
                status=s['status'],
                due_date=today + datetime.timedelta(days=s['due_offset']),
                created_at=mrs.created_at,
                
                # Snapshot details
                company_name=profile.name if profile else "TEXKNIT COLORS",
                company_address=profile.address if profile else "",
                company_gstin=profile.gstin if profile else "",
                company_email=profile.email if profile else "",
                company_phone=profile.phone if profile else ""
            )

    print(f"Successfully generated {invoice_count} detailed invoices.")
    print("- Paid: 3")
    print("- Sent: 4")
    print("- Draft: 3")
    print("- Overdue (Sent & Past Due): 5")
    db.close()

if __name__ == "__main__":
    seed_data()
