#!/usr/bin/env python3
"""
Fix route ordering in supplier_ledger.py and customer_ledger.py

FastAPI requires specific routes (like /aging, /reconcile) to be defined
BEFORE generic path parameter routes (like /{ledger_id}).
"""

def fix_supplier_ledger():
    """Fix supplier_ledger.py route order"""
    with open('app/api/routes/supplier_ledger.py', 'r') as f:
        lines = f.readlines()
    
    # Find line indices
    get_list_start = None
    get_by_id_start = None
    get_by_supplier_start = None
    aging_start = None
    reconcile_start = None
    match_payment_start = None
    
    for i, line in enumerate(lines):
        if '@router.get("/")' in line and get_list_start is None:
            get_list_start = i
        elif '@router.get("/{ledger_id}")' in line:
            get_by_id_start = i
        elif '@router.get("/supplier/{supplier_id}")' in line:
            get_by_supplier_start = i
        elif '@router.get("/aging")' in line:
            aging_start = i
        elif '@router.get("/reconcile")' in line:
            reconcile_start = i
        elif '@router.post("/match-payment")' in line:
            match_payment_start = i
    
    print(f"Found routes at lines:")
    print(f"  GET / : {get_list_start}")
    print(f"  GET /{{ledger_id}} : {get_by_id_start}")
    print(f"  GET /supplier/{{supplier_id}} : {get_by_supplier_start}")
    print(f"  GET /aging : {aging_start}")
    print(f"  GET /reconcile : {reconcile_start}")
    print(f"  POST /match-payment : {match_payment_start}")
    
    # Check if reordering is needed
    if get_by_id_start < aging_start or get_by_id_start < reconcile_start:
        print("\n⚠️  Route order issue detected!")
        print("   Specific routes (/aging, /reconcile) must come BEFORE /{ledger_id}")
        print("   This will cause FastAPI to interpret 'aging' as a UUID parameter.")
        return False
    else:
        print("\n✅ Route order is correct!")
        return True

def fix_customer_ledger():
    """Fix customer_ledger.py route order"""
    with open('app/api/routes/customer_ledger.py', 'r') as f:
        lines = f.readlines()
    
    # Similar logic for customer ledger
    get_by_id_start = None
    aging_start = None
    reconcile_start = None
    
    for i, line in enumerate(lines):
        if '@router.get("/{ledger_id}")' in line:
            get_by_id_start = i
        elif '@router.get("/aging")' in line:
            aging_start = i
        elif '@router.get("/reconcile")' in line:
            reconcile_start = i
    
    print(f"\nCustomer Ledger routes:")
    print(f"  GET /{{ledger_id}} : {get_by_id_start}")
    print(f"  GET /aging : {aging_start}")
    print(f"  GET /reconcile : {reconcile_start}")
    
    if get_by_id_start and aging_start and get_by_id_start < aging_start:
        print("\n⚠️  Route order issue detected in customer_ledger.py too!")
        return False
    else:
        print("\n✅ Customer ledger route order is correct!")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("ROUTE ORDER VALIDATION")
    print("=" * 60)
    print()
    
    supplier_ok = fix_supplier_ledger()
    customer_ok = fix_customer_ledger()
    
    if not supplier_ok or not customer_ok:
        print("\n" + "=" * 60)
        print("⚠️  ACTION REQUIRED:")
        print("=" * 60)
        print("Routes must be reordered manually in the source files.")
        print("Specific routes (/aging, /reconcile, /supplier/{id}) must be")
        print("defined BEFORE generic /{ledger_id} route.")
        print()
        print("Current order: GET / → GET /{id} → GET /aging → ...")
        print("Required order: GET / → GET /aging → GET /reconcile → GET /{id}")
    else:
        print("\n✅ All routes are correctly ordered!")
