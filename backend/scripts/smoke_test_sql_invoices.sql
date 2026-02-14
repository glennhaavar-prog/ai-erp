-- Create 5 test vendor invoices for smoke test
-- Client: GHB AS Test (09409ccf-d23e-45e5-93b9-68add0b96277)

-- Insert test vendors if they don't exist
INSERT INTO vendors (id, client_id, name, org_number, is_active)
VALUES 
    ('11111111-1111-1111-1111-111111111111'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, 'Kontorrekvisita AS', '987654321', true),
    ('22222222-2222-2222-2222-222222222222'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, 'Strømleverandøren', '876543210', true),
    ('33333333-3333-3333-3333-333333333333'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, 'IT-Utstyr Norge', '765432109', true),
    ('44444444-4444-4444-4444-444444444444'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, 'Møbel & Inventar', '654321098', true),
    ('55555555-5555-5555-5555-555555555555'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, 'Revisjon & Rådgivning', '543210987', true)
ON CONFLICT (id) DO NOTHING;

-- Insert test invoices
INSERT INTO vendor_invoices (
    id, client_id, vendor_id, invoice_number, invoice_date, due_date,
    amount_excl_vat, vat_amount, total_amount, currency, payment_status, review_status
)
VALUES 
    ('aaaaaaaa-1111-1111-1111-111111111111'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, '11111111-1111-1111-1111-111111111111'::uuid, 
     'TEST-001', '2026-02-11', '2026-03-13', 1000.00, 250.00, 1250.00, 'NOK', 'unpaid'::payment_status_enum, 'pending'),
    
    ('aaaaaaaa-2222-2222-2222-222222222222'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, '22222222-2222-2222-2222-222222222222'::uuid, 
     'TEST-002', '2026-02-10', '2026-03-12', 2000.00, 500.00, 2500.00, 'NOK', 'unpaid'::payment_status_enum, 'pending'),
    
    ('aaaaaaaa-3333-3333-3333-333333333333'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, '33333333-3333-3333-3333-333333333333'::uuid, 
     'TEST-003', '2026-02-09', '2026-03-11', 3000.00, 750.00, 3750.00, 'NOK', 'unpaid'::payment_status_enum, 'pending'),
    
    ('aaaaaaaa-4444-4444-4444-444444444444'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, '44444444-4444-4444-4444-444444444444'::uuid, 
     'TEST-004', '2026-02-08', '2026-03-10', 4000.00, 1000.00, 5000.00, 'NOK', 'unpaid'::payment_status_enum, 'pending'),
    
    ('aaaaaaaa-5555-5555-5555-555555555555'::uuid, '09409ccf-d23e-45e5-93b9-68add0b96277'::uuid, '55555555-5555-5555-5555-555555555555'::uuid, 
     'TEST-005', '2026-02-07', '2026-03-09', 5000.00, 1250.00, 6250.00, 'NOK', 'unpaid'::payment_status_enum, 'pending')
ON CONFLICT (id) DO NOTHING;

-- Show created invoices
SELECT 
    vi.id,
    vi.invoice_number,
    v.name as vendor_name,
    vi.total_amount,
    vi.invoice_date,
    vi.payment_status,
    vi.review_status
FROM vendor_invoices vi
JOIN vendors v ON vi.vendor_id = v.id
WHERE vi.invoice_number LIKE 'TEST-%'
ORDER BY vi.invoice_number;
