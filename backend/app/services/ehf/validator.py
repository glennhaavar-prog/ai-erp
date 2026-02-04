"""
EHF XML Validator
Validates EHF 3.0 XML against UBL 2.1 schema and PEPPOL rules
"""

from lxml import etree
from typing import List, Tuple
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)

# PEPPOL validation rules (business rules)
class ValidationRule:
    """Single validation rule"""
    def __init__(self, code: str, message: str, severity: str = "error"):
        self.code = code
        self.message = message
        self.severity = severity  # "error" or "warning"


class EHFValidator:
    """
    Validator for EHF 3.0 XML
    
    Validates:
    1. XML well-formedness
    2. UBL 2.1 schema compliance
    3. PEPPOL business rules
    4. Norwegian EHF specific rules
    """
    
    def __init__(self, schema_path: str = None):
        """
        Initialize validator
        
        Args:
            schema_path: Path to UBL 2.1 XSD schema (optional)
        """
        self.schema = None
        if schema_path and Path(schema_path).exists():
            try:
                schema_doc = etree.parse(schema_path)
                self.schema = etree.XMLSchema(schema_doc)
                logger.info("xsd_schema_loaded", path=schema_path)
            except Exception as e:
                logger.warning("failed_to_load_schema", path=schema_path, error=str(e))
    
    def validate(self, xml_content: str) -> Tuple[bool, List[ValidationRule]]:
        """
        Validate EHF XML
        
        Args:
            xml_content: EHF XML string
            
        Returns:
            (is_valid, list of validation errors/warnings)
        """
        errors = []
        warnings = []
        
        # Step 1: Check well-formedness
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            errors.append(ValidationRule(
                code="XML-001",
                message=f"XML is not well-formed: {str(e)}",
                severity="error"
            ))
            return False, errors
        
        # Step 2: Schema validation (if schema available)
        if self.schema:
            try:
                self.schema.assertValid(root)
                logger.debug("xsd_validation_passed")
            except etree.DocumentInvalid as e:
                errors.append(ValidationRule(
                    code="XSD-001",
                    message=f"Schema validation failed: {str(e)}",
                    severity="error"
                ))
                # Continue with business rules even if schema fails
        
        # Step 3: Business rules validation
        business_errors, business_warnings = self._validate_business_rules(root)
        errors.extend(business_errors)
        warnings.extend(business_warnings)
        
        # Step 4: Norwegian specific rules
        norwegian_errors, norwegian_warnings = self._validate_norwegian_rules(root)
        errors.extend(norwegian_errors)
        warnings.extend(norwegian_warnings)
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("ehf_validation_passed", warnings=len(warnings))
        else:
            logger.warning("ehf_validation_failed", errors=len(errors), warnings=len(warnings))
        
        return is_valid, errors + warnings
    
    def _validate_business_rules(self, root) -> Tuple[List[ValidationRule], List[ValidationRule]]:
        """
        Validate PEPPOL BIS Billing 3.0 business rules
        
        These are the core PEPPOL validation rules that must be met.
        """
        errors = []
        warnings = []
        namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        }
        
        # BR-01: Invoice must have invoice number
        # Check for root-level ID (not InvoiceLine/ID)
        invoice_id = root.xpath("/*/cbc:ID", namespaces=namespaces)
        if not invoice_id or not invoice_id[0].text:
            errors.append(ValidationRule(
                code="BR-01",
                message="Invoice must have an invoice number (cbc:ID)",
                severity="error"
            ))
        
        # BR-02: Invoice must have issue date
        issue_date = root.xpath("//cbc:IssueDate", namespaces=namespaces)
        if not issue_date or not issue_date[0].text:
            errors.append(ValidationRule(
                code="BR-02",
                message="Invoice must have an issue date (cbc:IssueDate)",
                severity="error"
            ))
        
        # BR-03: Invoice must have currency code
        currency = root.xpath("//cbc:DocumentCurrencyCode", namespaces=namespaces)
        if not currency or not currency[0].text:
            errors.append(ValidationRule(
                code="BR-03",
                message="Invoice must have a currency code (cbc:DocumentCurrencyCode)",
                severity="error"
            ))
        
        # BR-04: Invoice must have supplier information
        supplier = root.xpath("//cac:AccountingSupplierParty/cac:Party", namespaces=namespaces)
        if not supplier:
            errors.append(ValidationRule(
                code="BR-04",
                message="Invoice must have supplier party (cac:AccountingSupplierParty)",
                severity="error"
            ))
        else:
            # BR-05: Supplier must have name
            supplier_name = supplier[0].xpath(".//cac:PartyName/cbc:Name | .//cac:PartyLegalEntity/cbc:RegistrationName", namespaces=namespaces)
            if not supplier_name or not supplier_name[0].text:
                errors.append(ValidationRule(
                    code="BR-05",
                    message="Supplier must have a name",
                    severity="error"
                ))
        
        # BR-06: Invoice must have customer information
        customer = root.xpath("//cac:AccountingCustomerParty/cac:Party", namespaces=namespaces)
        if not customer:
            errors.append(ValidationRule(
                code="BR-06",
                message="Invoice must have customer party (cac:AccountingCustomerParty)",
                severity="error"
            ))
        else:
            # BR-07: Customer must have name
            customer_name = customer[0].xpath(".//cac:PartyName/cbc:Name | .//cac:PartyLegalEntity/cbc:RegistrationName", namespaces=namespaces)
            if not customer_name or not customer_name[0].text:
                errors.append(ValidationRule(
                    code="BR-07",
                    message="Customer must have a name",
                    severity="error"
                ))
        
        # BR-08: Invoice must have at least one line
        lines = root.xpath("//cac:InvoiceLine | //cac:CreditNoteLine", namespaces=namespaces)
        if not lines:
            errors.append(ValidationRule(
                code="BR-08",
                message="Invoice must have at least one invoice line",
                severity="error"
            ))
        
        # BR-09: Invoice must have totals
        monetary_total = root.xpath("//cac:LegalMonetaryTotal", namespaces=namespaces)
        if not monetary_total:
            errors.append(ValidationRule(
                code="BR-09",
                message="Invoice must have monetary totals (cac:LegalMonetaryTotal)",
                severity="error"
            ))
        
        # BR-10: Invoice must have tax total
        tax_total = root.xpath("//cac:TaxTotal", namespaces=namespaces)
        if not tax_total:
            errors.append(ValidationRule(
                code="BR-10",
                message="Invoice must have tax total (cac:TaxTotal)",
                severity="error"
            ))
        
        # BR-11: Sum of line amounts must equal line extension amount
        if lines and monetary_total:
            line_amounts = root.xpath("//cac:InvoiceLine/cbc:LineExtensionAmount | //cac:CreditNoteLine/cbc:LineExtensionAmount", namespaces=namespaces)
            if line_amounts:
                sum_lines = sum(float(amt.text) for amt in line_amounts if amt.text)
                line_extension = root.xpath("//cac:LegalMonetaryTotal/cbc:LineExtensionAmount", namespaces=namespaces)
                if line_extension and line_extension[0].text:
                    total = float(line_extension[0].text)
                    if abs(sum_lines - total) > 0.01:  # Allow 1 øre rounding
                        errors.append(ValidationRule(
                            code="BR-11",
                            message=f"Sum of line amounts ({sum_lines}) does not equal line extension amount ({total})",
                            severity="error"
                        ))
        
        # BR-12: Tax inclusive amount = tax exclusive amount + tax amount
        if monetary_total and tax_total:
            tax_exclusive = root.xpath("//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount", namespaces=namespaces)
            tax_inclusive = root.xpath("//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount", namespaces=namespaces)
            tax_amount = root.xpath("//cac:TaxTotal/cbc:TaxAmount", namespaces=namespaces)
            
            if tax_exclusive and tax_inclusive and tax_amount:
                excl = float(tax_exclusive[0].text) if tax_exclusive[0].text else 0
                incl = float(tax_inclusive[0].text) if tax_inclusive[0].text else 0
                tax = float(tax_amount[0].text) if tax_amount[0].text else 0
                
                expected = excl + tax
                if abs(incl - expected) > 0.01:
                    errors.append(ValidationRule(
                        code="BR-12",
                        message=f"Tax inclusive amount ({incl}) != tax exclusive ({excl}) + tax ({tax})",
                        severity="error"
                    ))
        
        # BR-W01: Warning if no due date
        due_date = root.xpath("//cbc:DueDate", namespaces=namespaces)
        if not due_date or not due_date[0].text:
            warnings.append(ValidationRule(
                code="BR-W01",
                message="Invoice should have a due date (cbc:DueDate)",
                severity="warning"
            ))
        
        return errors, warnings
    
    def _validate_norwegian_rules(self, root) -> Tuple[List[ValidationRule], List[ValidationRule]]:
        """
        Validate Norwegian-specific EHF rules
        """
        errors = []
        warnings = []
        namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        }
        
        # NO-01: Supplier should have Norwegian org.nr
        supplier_id = root.xpath("//cac:AccountingSupplierParty//cac:PartyLegalEntity/cbc:CompanyID", namespaces=namespaces)
        if supplier_id and supplier_id[0].text:
            org_nr = supplier_id[0].text.strip()
            if not self._is_valid_norwegian_org_nr(org_nr):
                warnings.append(ValidationRule(
                    code="NO-01",
                    message=f"Supplier company ID ({org_nr}) does not appear to be a valid Norwegian organization number",
                    severity="warning"
                ))
        
        # NO-02: Currency should be NOK for Norwegian invoices
        currency = root.xpath("//cbc:DocumentCurrencyCode", namespaces=namespaces)
        if currency and currency[0].text and currency[0].text != "NOK":
            warnings.append(ValidationRule(
                code="NO-02",
                message=f"Currency is {currency[0].text}, expected NOK for Norwegian invoices",
                severity="warning"
            ))
        
        # NO-03: Endpoint ID scheme should be 0192 (Norwegian org.nr)
        endpoint_scheme = root.xpath("//cac:AccountingSupplierParty//cbc:EndpointID/@schemeID", namespaces=namespaces)
        if endpoint_scheme and endpoint_scheme[0] != "0192":
            warnings.append(ValidationRule(
                code="NO-03",
                message=f"Endpoint ID scheme is {endpoint_scheme[0]}, expected 0192 for Norwegian organizations",
                severity="warning"
            ))
        
        # NO-04: Check VAT rates are Norwegian standard rates
        tax_percents = root.xpath("//cac:TaxCategory/cbc:Percent", namespaces=namespaces)
        valid_rates = ["0.00", "0", "12.00", "12", "15.00", "15", "25.00", "25"]
        for percent in tax_percents:
            if percent.text and percent.text not in valid_rates:
                warnings.append(ValidationRule(
                    code="NO-04",
                    message=f"Tax rate {percent.text}% is not a standard Norwegian VAT rate (0%, 12%, 15%, or 25%)",
                    severity="warning"
                ))
        
        return errors, warnings
    
    def _is_valid_norwegian_org_nr(self, org_nr: str) -> bool:
        """
        Validate Norwegian organization number format
        
        Format: 9 digits, with mod11 checksum
        """
        # Remove spaces
        org_nr = org_nr.replace(" ", "").replace("-", "")
        
        # Must be 9 digits
        if not org_nr.isdigit() or len(org_nr) != 9:
            return False
        
        # Validate mod11 checksum
        weights = [3, 2, 7, 6, 5, 4, 3, 2]
        sum_val = sum(int(org_nr[i]) * weights[i] for i in range(8))
        remainder = sum_val % 11
        
        if remainder == 0:
            check_digit = 0
        else:
            check_digit = 11 - remainder
        
        # If check digit is 10, org.nr is invalid
        if check_digit == 10:
            return False
        
        return int(org_nr[8]) == check_digit


def validate_ehf_xml(xml_content: str, schema_path: str = None) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate EHF XML
    
    Args:
        xml_content: EHF XML string
        schema_path: Optional path to XSD schema
        
    Returns:
        (is_valid, list of error/warning messages)
    """
    validator = EHFValidator(schema_path)
    is_valid, rules = validator.validate(xml_content)
    
    messages = [f"[{rule.severity.upper()}] {rule.code}: {rule.message}" for rule in rules]
    
    return is_valid, messages
