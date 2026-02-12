# Read the file
with open('app/api/routes/supplier_ledger.py', 'r') as f:
    content = f.read()

# Find the export endpoints section
export_start = content.find('# ==================== EXPORT ENDPOINTS ====================')
if export_start == -1:
    print("Export endpoints not found!")
    exit(1)

# Extract export endpoints section
export_section = content[export_start:]

# Remove export endpoints from current position
content_without_exports = content[:export_start].rstrip()

# Find the position of @router.get("/{ledger_id}")
ledger_id_pos = content_without_exports.find('@router.get("/{ledger_id}")')
if ledger_id_pos == -1:
    print("ledger_id route not found!")
    exit(1)

# Insert export endpoints BEFORE the ledger_id route
new_content = content_without_exports[:ledger_id_pos] + '\n\n' + export_section + '\n\n' + content_without_exports[ledger_id_pos:]

# Write back
with open('app/api/routes/supplier_ledger.py', 'w') as f:
    f.write(new_content)

print("Fixed supplier_ledger.py - moved export endpoints before /{ledger_id} route")
