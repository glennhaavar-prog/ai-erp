"""
Anomaly Detection Service - Flag Unusual Transactions

Detects:
1. Amount outliers (>3 standard deviations from vendor's average)
2. Duplicate invoices (same amount + vendor within 7 days)
3. Weekend/holiday bookings (unusual patterns)
4. Suspicious patterns (round amounts, too frequent, etc.)

Adds "flagged" field to vendor_invoice and shows warnings in Review Queue.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime, timedelta, date
import uuid
from decimal import Decimal
import statistics

from app.models import VendorInvoice, Vendor, BankTransaction


class AnomalyFlag:
    """Represents an anomaly detection"""
    def __init__(
        self,
        flag_type: str,
        severity: str,  # low/medium/high
        message: str,
        details: Dict[str, Any] = None
    ):
        self.flag_type = flag_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flag_type": self.flag_type,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class AnomalyDetectionService:
    """
    Anomaly Detection Service
    
    Analyzes vendor invoices and bank transactions for unusual patterns
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Configuration
        self.outlier_std_threshold = 3.0  # Standard deviations for outlier
        self.duplicate_window_days = 7  # Days to check for duplicates
        self.round_amount_threshold = 1000  # Flag round amounts >= this
        self.min_samples_for_outlier = 5  # Need at least N samples
    
    async def detect_anomalies(
        self,
        vendor_invoice: VendorInvoice
    ) -> List[AnomalyFlag]:
        """
        Detect all anomalies for a vendor invoice
        
        Returns list of anomaly flags
        """
        flags = []
        
        # 1. Amount outlier detection
        outlier_flag = await self._detect_amount_outlier(vendor_invoice)
        if outlier_flag:
            flags.append(outlier_flag)
        
        # 2. Duplicate invoice detection
        duplicate_flag = await self._detect_duplicate_invoice(vendor_invoice)
        if duplicate_flag:
            flags.append(duplicate_flag)
        
        # 3. Weekend/holiday booking
        weekend_flag = self._detect_weekend_booking(vendor_invoice)
        if weekend_flag:
            flags.append(weekend_flag)
        
        # 4. Round amount detection
        round_flag = self._detect_round_amount(vendor_invoice)
        if round_flag:
            flags.append(round_flag)
        
        # 5. Frequent invoices from same vendor
        frequent_flag = await self._detect_frequent_invoices(vendor_invoice)
        if frequent_flag:
            flags.append(frequent_flag)
        
        return flags
    
    async def _detect_amount_outlier(
        self,
        vendor_invoice: VendorInvoice
    ) -> Optional[AnomalyFlag]:
        """
        Detect if invoice amount is >3 std dev from vendor's average
        
        Statistical outlier detection
        """
        if not vendor_invoice.vendor_id:
            return None
        
        # Get historical amounts for this vendor
        query = select(VendorInvoice.total_amount).where(
            and_(
                VendorInvoice.vendor_id == vendor_invoice.vendor_id,
                VendorInvoice.id != vendor_invoice.id,  # Exclude current
                VendorInvoice.total_amount > 0
            )
        )
        
        result = await self.db.execute(query)
        amounts = [float(row[0]) for row in result.all()]
        
        if len(amounts) < self.min_samples_for_outlier:
            # Not enough data for statistical analysis
            return None
        
        # Calculate statistics
        mean = statistics.mean(amounts)
        try:
            stdev = statistics.stdev(amounts)
        except statistics.StatisticsError:
            # All values identical (stdev = 0)
            stdev = 0
        
        if stdev == 0:
            # All historical amounts are identical
            current_amount = float(vendor_invoice.total_amount)
            if current_amount != mean:
                return AnomalyFlag(
                    flag_type="amount_outlier",
                    severity="high",
                    message=f"Amount {current_amount:,.2f} differs from vendor's standard amount {mean:,.2f}",
                    details={
                        "current_amount": current_amount,
                        "typical_amount": mean,
                        "historical_count": len(amounts)
                    }
                )
            return None
        
        # Calculate z-score
        current_amount = float(vendor_invoice.total_amount)
        z_score = abs((current_amount - mean) / stdev)
        
        if z_score > self.outlier_std_threshold:
            # This is an outlier!
            severity = "high" if z_score > 5 else "medium"
            
            return AnomalyFlag(
                flag_type="amount_outlier",
                severity=severity,
                message=f"Amount {current_amount:,.2f} is unusual (avg: {mean:,.2f}, std dev: {z_score:.1f})",
                details={
                    "current_amount": current_amount,
                    "average_amount": mean,
                    "std_deviation": stdev,
                    "z_score": z_score,
                    "historical_count": len(amounts)
                }
            )
        
        return None
    
    async def _detect_duplicate_invoice(
        self,
        vendor_invoice: VendorInvoice
    ) -> Optional[AnomalyFlag]:
        """
        Detect duplicate invoices
        
        Same vendor + same amount within 7 days
        """
        if not vendor_invoice.vendor_id:
            return None
        
        # Look for similar invoices
        date_from = vendor_invoice.invoice_date - timedelta(days=self.duplicate_window_days)
        date_to = vendor_invoice.invoice_date + timedelta(days=self.duplicate_window_days)
        
        query = select(VendorInvoice).where(
            and_(
                VendorInvoice.vendor_id == vendor_invoice.vendor_id,
                VendorInvoice.id != vendor_invoice.id,
                VendorInvoice.total_amount == vendor_invoice.total_amount,
                VendorInvoice.invoice_date.between(date_from, date_to)
            )
        )
        
        result = await self.db.execute(query)
        duplicates = result.scalars().all()
        
        if duplicates:
            duplicate_numbers = [inv.invoice_number for inv in duplicates]
            
            return AnomalyFlag(
                flag_type="duplicate_invoice",
                severity="high",
                message=f"Possible duplicate: same amount ({vendor_invoice.total_amount}) within {self.duplicate_window_days} days",
                details={
                    "amount": float(vendor_invoice.total_amount),
                    "similar_invoices": duplicate_numbers,
                    "count": len(duplicates)
                }
            )
        
        return None
    
    def _detect_weekend_booking(
        self,
        vendor_invoice: VendorInvoice
    ) -> Optional[AnomalyFlag]:
        """
        Detect bookings on weekends
        
        Weekends are unusual for invoice processing
        """
        # Check if invoice_date is weekend
        weekday = vendor_invoice.invoice_date.weekday()
        
        if weekday >= 5:  # Saturday=5, Sunday=6
            day_name = "Saturday" if weekday == 5 else "Sunday"
            
            return AnomalyFlag(
                flag_type="weekend_booking",
                severity="low",
                message=f"Invoice dated on {day_name}",
                details={
                    "invoice_date": vendor_invoice.invoice_date.isoformat(),
                    "day_of_week": day_name
                }
            )
        
        return None
    
    def _detect_round_amount(
        self,
        vendor_invoice: VendorInvoice
    ) -> Optional[AnomalyFlag]:
        """
        Detect suspiciously round amounts
        
        Very round amounts (10000, 50000) can be fraudulent
        """
        amount = float(vendor_invoice.total_amount)
        
        if amount >= self.round_amount_threshold:
            # Check if it's a very round number
            if amount % 10000 == 0:
                severity = "medium" if amount >= 50000 else "low"
                return AnomalyFlag(
                    flag_type="round_amount",
                    severity=severity,
                    message=f"Very round amount: {amount:,.0f}",
                    details={
                        "amount": amount,
                        "note": "Round amounts may warrant verification"
                    }
                )
            elif amount % 1000 == 0 and amount >= 10000:
                return AnomalyFlag(
                    flag_type="round_amount",
                    severity="low",
                    message=f"Round amount: {amount:,.0f}",
                    details={
                        "amount": amount
                    }
                )
        
        return None
    
    async def _detect_frequent_invoices(
        self,
        vendor_invoice: VendorInvoice
    ) -> Optional[AnomalyFlag]:
        """
        Detect if too many invoices from same vendor in short period
        
        More than 5 invoices in one week might be unusual
        """
        if not vendor_invoice.vendor_id:
            return None
        
        # Count invoices in past 7 days
        date_from = vendor_invoice.invoice_date - timedelta(days=7)
        
        query = select(func.count()).select_from(VendorInvoice).where(
            and_(
                VendorInvoice.vendor_id == vendor_invoice.vendor_id,
                VendorInvoice.invoice_date >= date_from,
                VendorInvoice.invoice_date <= vendor_invoice.invoice_date
            )
        )
        
        result = await self.db.execute(query)
        count = result.scalar()
        
        if count > 5:
            return AnomalyFlag(
                flag_type="frequent_invoices",
                severity="low",
                message=f"{count} invoices from this vendor in the past week",
                details={
                    "invoice_count": count,
                    "period_days": 7
                }
            )
        
        return None
    
    async def update_invoice_flags(
        self,
        invoice_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Detect and update anomaly flags for an invoice
        
        Stores flags in ai_detected_issues array
        Returns list of flag dicts
        """
        # Get invoice
        result = await self.db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return []
        
        # Detect anomalies
        flags = await self.detect_anomalies(invoice)
        
        if flags:
            # Store flags in invoice
            flag_strings = [f"{flag.severity.upper()}: {flag.message}" for flag in flags]
            invoice.ai_detected_issues = flag_strings
            
            # Lower confidence if high-severity flags
            high_severity_count = sum(1 for f in flags if f.severity == "high")
            if high_severity_count > 0 and invoice.ai_confidence_score:
                # Reduce confidence by 20 per high-severity flag
                reduction = min(50, high_severity_count * 20)
                invoice.ai_confidence_score = max(0, invoice.ai_confidence_score - reduction)
            
            # Mark for review if high severity
            if high_severity_count > 0:
                invoice.review_status = "needs_review"
            
            invoice.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(invoice)
        
        return [flag.to_dict() for flag in flags]
    
    async def get_invoice_risk_score(
        self,
        invoice_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Calculate overall risk score for an invoice
        
        Returns:
        {
            "risk_score": 0-100,  # Higher = more risky
            "risk_level": "low/medium/high",
            "flags": [...],
            "recommendation": "approve/review/reject"
        }
        """
        result = await self.db.execute(
            select(VendorInvoice).where(VendorInvoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return {"risk_score": 0, "risk_level": "unknown", "flags": []}
        
        # Detect anomalies
        flags = await self.detect_anomalies(invoice)
        
        # Calculate risk score
        risk_score = 0
        
        severity_weights = {
            "low": 10,
            "medium": 25,
            "high": 40
        }
        
        for flag in flags:
            risk_score += severity_weights.get(flag.severity, 10)
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = "high"
            recommendation = "review"
        elif risk_score >= 30:
            risk_level = "medium"
            recommendation = "review"
        else:
            risk_level = "low"
            recommendation = "approve"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": [flag.to_dict() for flag in flags],
            "recommendation": recommendation,
            "invoice_id": str(invoice_id)
        }


# Helper functions
async def detect_invoice_anomalies(
    db: AsyncSession,
    invoice_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    Convenience function to detect anomalies for an invoice
    """
    service = AnomalyDetectionService(db)
    return await service.update_invoice_flags(invoice_id)


async def get_risk_score(
    db: AsyncSession,
    invoice_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Get risk assessment for an invoice
    """
    service = AnomalyDetectionService(db)
    return await service.get_invoice_risk_score(invoice_id)
