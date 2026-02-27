from peewee import *
import datetime
import os

db = SqliteDatabase('consultancy.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    role = CharField() # ADMIN, SUPERVISOR, STORE_MANAGER
    created_at = DateTimeField(default=datetime.datetime.now)

class Supplier(BaseModel):
    name = CharField()
    contact_person = CharField()
    phone = CharField()
    material_categories = TextField() # Store as comma-separated or JSON string
    gst_no = CharField(null=True)
    rating = FloatField(default=0.0)
    rating_count = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class Material(BaseModel):
    name = CharField()
    code = CharField(null=True)
    category = CharField(default='CHEMICAL') # DYE, CHEMICAL
    unit = CharField() # kg, ltr, pcs
    quantity = FloatField(default=0.0)
    min_stock = FloatField(default=10.0)
    unit_cost = FloatField(default=0.0)
    abc_category = CharField(default='None') # A, B, C, None
    supplier = ForeignKeyField(Supplier, backref='materials', null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

class MRS(BaseModel):
    batch_id = CharField()
    supervisor = ForeignKeyField(User, backref='material_requests')
    status = CharField(default='PENDING') # PENDING, ISSUED, REJECTED, PARTIALLY_ISSUED
    created_at = DateTimeField(default=datetime.datetime.now)

class MRSItem(BaseModel):
    mrs = ForeignKeyField(MRS, backref='items')
    material = ForeignKeyField(Material, backref='mrs_items')
    quantity_requested = FloatField()
    quantity_issued = FloatField(default=0.0)

class ProductInward(BaseModel):
    store_manager = ForeignKeyField(User, backref='indents_raised')
    supplier = ForeignKeyField(Supplier, backref='indents')
    admin = ForeignKeyField(User, backref='indents_approved', null=True)
    status = CharField(default='RAISED') # RAISED, APPROVED, REJECTED, COMPLETED
    reason = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    approved_at = DateTimeField(null=True)
    approval_remarks = TextField(null=True)
    completed_at = DateTimeField(null=True)

class PIItem(BaseModel):
    pi = ForeignKeyField(ProductInward, backref='items')
    material = ForeignKeyField(Material, backref='pi_items')
    quantity = FloatField()
    unit_price = FloatField(default=0.0)

class Transaction(BaseModel):
    type = CharField() # ISSUE, INWARD, ADJUSTMENT, RETURN
    material = ForeignKeyField(Material, backref='transactions')
    quantity = FloatField()
    related_id = IntegerField(null=True) # ID of MRS or PI
    performed_by = ForeignKeyField(User, backref='transactions')
    timestamp = DateTimeField(default=datetime.datetime.now)

class AuditLog(BaseModel):
    action = CharField()
    user = ForeignKeyField(User, backref='audit_logs', null=True)
    details = TextField(null=True) # JSON string
    timestamp = DateTimeField(default=datetime.datetime.now)

class Invoice(BaseModel):
    invoice_no = CharField(unique=True)
    mrs = ForeignKeyField(MRS, backref='invoices')
    total_amount = FloatField(default=0.0)
    tax_amount = FloatField(default=0.0)
    grand_total = FloatField(default=0.0)
    client_name = CharField(null=True)
    client_address = TextField(null=True)
    client_gstin = CharField(null=True)
    gst_percentage = FloatField(default=18)  # default GST%
    status = CharField(default='DRAFT') # DRAFT, SENT, PAID
    created_at = DateTimeField(default=datetime.datetime.now)

    # Snapshots for immutability
    company_name = CharField(null=True)
    company_address = TextField(null=True)
    company_gstin = CharField(null=True)
    company_email = CharField(null=True)
    company_phone = CharField(null=True)
    company_logo_data = TextField(null=True) # Base64 snapshot
    due_date = DateField(null=True)

class Consumer(BaseModel):
    company_name = CharField()
    contact_person = CharField()
    phone = CharField()
    gst_no = CharField(null=True)
    location = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class CompanyProfile(BaseModel):
    name = CharField(default="TEXKNIT COLORS")
    address = TextField(default="123 Textile Park, Tirupur - 641601")
    gstin = CharField(default="33AAAAA0000A1Z5")
    email = CharField(default="accounts@texknit.com")
    phone = CharField(default="+91 98765 43210")
    logo_path = CharField(null=True)
    default_tax_rate = FloatField(default=18.0)
    daily_late_fee = FloatField(default=0.0)

def initialize_db():
    db.connect()
    db.create_tables([
        User, Supplier, Material, MRS, MRSItem, 
        ProductInward, PIItem, Transaction, AuditLog, Invoice, CompanyProfile, Consumer
    ])
    
    # Create default admin if not exists
    if User.select().where(User.username == 'admin').count() == 0:
        User.create(username='admin', password='admin123', role='ADMIN') # Note: Should hash in production
    
    # Ensure at least one company profile exists
    if CompanyProfile.select().count() == 0:
        CompanyProfile.create()
        
    db.close()

if __name__ == '__main__':
    initialize_db()
