"""
Voucher model - Alias for GeneralLedger (for backward compatibility)

In Norwegian accounting, "Bilag" (Voucher) = Journal Entry = GeneralLedger
This is just an alias to the GeneralLedger model for services that expect a Voucher class.
"""
from app.models.general_ledger import GeneralLedger, GeneralLedgerLine

# Voucher is an alias for GeneralLedger
Voucher = GeneralLedger
VoucherLine = GeneralLedgerLine

__all__ = ['Voucher', 'VoucherLine']
