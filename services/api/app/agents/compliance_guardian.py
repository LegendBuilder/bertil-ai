from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

from ..models import Verification, Entry, FiscalYear, ComplianceFlag
from ..compliance import run_verification_rules, compute_score, RuleFlag


class ComplianceRisk(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceGuardian:
    """PREVENTS compliance issues before they happen - Real-time Swedish compliance monitoring."""
    
    def __init__(self, session: AsyncSession, org_id: int):
        self.session = session
        self.org_id = org_id
        
        # Swedish compliance thresholds
        self.CASH_TRANSACTION_LIMIT = 15000  # SEK - suspicious transactions
        self.LATE_ENTRY_WARNING_DAYS = 5     # Days before flagging late entries
        self.MONTHLY_VAT_THRESHOLD = 1000000 # SEK - monthly VAT reporting required
        self.AUDIT_TRAIL_RETENTION = 7 * 365 # Days - 7 years retention
        
    async def pre_verification_check(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance BEFORE creating verification - prevent issues."""
        
        issues = []
        warnings = []
        risk_level = ComplianceRisk.LOW
        
        # 1. Immediate compliance validation
        immediate_issues = await self._check_immediate_compliance(verification_data)
        issues.extend(immediate_issues['errors'])
        warnings.extend(immediate_issues['warnings'])
        
        # 2. Pattern analysis - detect suspicious patterns
        pattern_analysis = await self._analyze_patterns(verification_data)
        if pattern_analysis['risk_level'].value > risk_level.value:
            risk_level = pattern_analysis['risk_level']
        warnings.extend(pattern_analysis['warnings'])
        
        # 3. Regulatory deadline checks
        deadline_checks = await self._check_regulatory_deadlines(verification_data)
        warnings.extend(deadline_checks)
        
        # 4. VAT compliance pre-check
        vat_compliance = await self._check_vat_compliance(verification_data)
        issues.extend(vat_compliance['errors'])
        warnings.extend(vat_compliance['warnings'])
        
        # 5. Document retention compliance
        retention_check = await self._check_document_retention(verification_data)
        warnings.extend(retention_check)
        
        # Determine if verification should be blocked
        should_block = len(issues) > 0 or risk_level == ComplianceRisk.CRITICAL
        
        return {
            "can_proceed": not should_block,
            "risk_level": risk_level.value,
            "issues": issues,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(issues, warnings),
            "compliance_score": self._calculate_compliance_score(issues, warnings)
        }
    
    async def _check_immediate_compliance(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Immediate Swedish compliance checks."""
        errors = []
        warnings = []
        
        total_amount = float(data.get('total_amount', 0))
        counterparty = data.get('counterparty', '')
        vat_amount = float(data.get('vat_amount', 0)) 
        verification_date = data.get('date')
        
        # R-001: Required fields check (before DB insertion)
        if not counterparty:
            errors.append("Motpart saknas (krävs enligt Bokföringslagen)")
        if total_amount <= 0:
            errors.append("Totalbelopp måste vara positivt")
        if not verification_date:
            errors.append("Datum saknas")
        if not data.get('document_link'):
            warnings.append("Underlag/kvitto saknas - krävs för revision")
            
        # R-011: Timeliness check
        if verification_date:
            try:
                v_date = date.fromisoformat(verification_date) if isinstance(verification_date, str) else verification_date
                days_old = (date.today() - v_date).days
                
                # Cash transactions must be recorded next business day
                entries = data.get('entries', [])
                has_cash = any(str(entry.get('account', '')).startswith('1910') for entry in entries)
                
                if has_cash and days_old > 1:
                    errors.append("Kassatransaktion måste bokföras nästa arbetsdag (Skatteverket)")
                elif days_old > 30:
                    warnings.append(f"Bokföring försenad ({days_old} dagar) - risk för Skatteverket anmärkning")
                    
            except (ValueError, TypeError):
                errors.append("Ogiltigt datum format")
        
        # Large cash transaction warning (money laundering prevention)
        if total_amount > self.CASH_TRANSACTION_LIMIT:
            entries = data.get('entries', [])
            has_cash = any(str(entry.get('account', '')).startswith('1910') for entry in entries)
            if has_cash:
                warnings.append(f"Stor kontanttransaktion ({total_amount} SEK) - dokumentera ursprung")
        
        # VAT consistency check
        if vat_amount > 0 and total_amount > 0:
            vat_rate = vat_amount / (total_amount - vat_amount)
            valid_rates = [0.25, 0.12, 0.06]  # Swedish VAT rates
            if not any(abs(vat_rate - rate) < 0.02 for rate in valid_rates):
                warnings.append(f"Ovanlig momssats ({vat_rate:.1%}) - kontrollera beräkning")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _analyze_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns to detect potential compliance risks."""
        warnings = []
        risk_level = ComplianceRisk.LOW
        
        counterparty = data.get('counterparty', '').lower()
        total_amount = float(data.get('total_amount', 0))
        
        # Check for duplicate vendor patterns (last 30 days)
        if counterparty:
            recent_date = date.today() - timedelta(days=30)
            stmt = select(func.count(Verification.id)).where(
                and_(
                    Verification.org_id == self.org_id,
                    func.lower(Verification.counterparty).like(f"%{counterparty}%"),
                    Verification.date >= recent_date,
                    func.abs(Verification.total_amount - total_amount) < 1.0  # Similar amounts
                )
            )
            
            similar_count = await self.session.execute(stmt)
            count = similar_count.scalar() or 0
            
            if count > 3:  # More than 3 similar transactions
                warnings.append(f"Upprepad transaktion pattern ({count} liknande på 30 dagar)")
                risk_level = ComplianceRisk.MEDIUM
        
        # Round number analysis (fraud indicator)
        if total_amount > 1000 and total_amount % 100 == 0:
            # Check if many round numbers recently
            recent_round_stmt = select(func.count(Verification.id)).where(
                and_(
                    Verification.org_id == self.org_id,
                    Verification.date >= date.today() - timedelta(days=30),
                    func.mod(Verification.total_amount, 100) == 0,
                    Verification.total_amount > 1000
                )
            )
            
            round_count = (await self.session.execute(recent_round_stmt)).scalar() or 0
            if round_count > 10:  # Many round numbers
                warnings.append("Många jämna belopp senaste månaden - granska för konstlade transaktioner")
        
        # Weekend/holiday transaction analysis
        if data.get('date'):
            v_date = date.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date']
            if v_date.weekday() >= 5:  # Weekend
                warnings.append("Helgtransaktion - kontrollera att datum är korrekt")
        
        return {"warnings": warnings, "risk_level": risk_level}
    
    async def _check_regulatory_deadlines(self, data: Dict[str, Any]) -> List[str]:
        """Check against Swedish regulatory deadlines."""
        warnings = []
        
        verification_date = data.get('date')
        if not verification_date:
            return warnings
            
        v_date = date.fromisoformat(verification_date) if isinstance(verification_date, str) else verification_date
        
        # Monthly VAT return deadline (12th of next month)
        last_month = (date.today().replace(day=1) - timedelta(days=1))
        vat_deadline = (last_month.replace(day=1) + timedelta(days=32)).replace(day=12)
        
        if v_date.month == last_month.month and date.today() > vat_deadline:
            warnings.append(f"Transaktion från {v_date} kan påverka försenad moms-deklaration")
        
        # Year-end closing deadlines
        if v_date.month == 12 and v_date.day > 25:
            warnings.append("Transaktion nära årsskifte - kontrollera bokföringsperiod")
        
        # Audit preparation period
        today = date.today()
        if today.month in [2, 3, 4]:  # Audit season
            warnings.append("Revision pågår - säkerställ fullständig dokumentation")
        
        return warnings
    
    async def _check_vat_compliance(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Advanced VAT compliance checking."""
        errors = []
        warnings = []
        
        vat_code = data.get('vat_code', '')
        entries = data.get('entries', [])
        total_amount = float(data.get('total_amount', 0))
        
        # Reverse charge validation
        if vat_code and vat_code.upper().startswith(('RC', 'EU-RC')):
            has_2615 = any(str(entry.get('account', '')).startswith('2615') for entry in entries)
            has_2645 = any(str(entry.get('account', '')).startswith('2645') for entry in entries)
            
            if not (has_2615 and has_2645):
                errors.append("Omvänd moms kräver både 2615 (utgående) och 2645 (ingående) konton")
        
        # EU transaction validation
        counterparty = data.get('counterparty', '').lower()
        eu_indicators = ['eu', 'germany', 'denmark', 'norway', 'finland']
        
        if any(indicator in counterparty for indicator in eu_indicators):
            if not vat_code or not vat_code.upper().startswith(('RC', 'EU')):
                warnings.append("EU-transaktion kan kräva omvänd moms - kontrollera VAT-nummer")
        
        # Monthly VAT threshold check
        if total_amount > self.MONTHLY_VAT_THRESHOLD / 30:  # Large daily transaction
            warnings.append("Stor transaktion - kontrollera månadsvis momsrapportering")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _check_document_retention(self, data: Dict[str, Any]) -> List[str]:
        """Check document retention compliance."""
        warnings = []
        
        document_link = data.get('document_link')
        if not document_link:
            warnings.append("Underlag saknas - krävs enligt 7-års arkiveringsplikt")
            return warnings
        
        # Check if document exists in WORM storage
        if document_link.startswith('/documents/'):
            # This would check actual WORM storage - placeholder for now
            warnings.append("Kontrollera att underlag arkiveras i WORM-lagring")
        
        return warnings
    
    def _generate_recommendations(self, issues: List[str], warnings: List[str]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if any('motpart' in issue.lower() for issue in issues):
            recommendations.append("Lägg till leverantörsnamn från kvitto/faktura")
            
        if any('datum' in issue.lower() for issue in issues):
            recommendations.append("Kontrollera transaktionsdatum mot kvitto")
            
        if any('moms' in warning.lower() for warning in warnings):
            recommendations.append("Granska momssats mot Skatteverkets tabell")
            
        if any('underlag' in warning.lower() for warning in warnings):
            recommendations.append("Bifoga digital kopia av kvitto/faktura")
            
        if any('försenad' in warning.lower() for warning in warnings):
            recommendations.append("Implementera daglig bokföringsrutin")
        
        return recommendations
    
    def _calculate_compliance_score(self, issues: List[str], warnings: List[str]) -> int:
        """Calculate compliance score (0-100)."""
        score = 100
        score -= len(issues) * 20  # Major penalty for errors
        score -= len(warnings) * 5  # Minor penalty for warnings
        return max(0, score)
    
    async def daily_compliance_monitoring(self) -> Dict[str, Any]:
        """Daily compliance health check."""
        
        # Check recent transactions for compliance drift
        recent_date = date.today() - timedelta(days=7)
        stmt = select(Verification).where(
            and_(
                Verification.org_id == self.org_id,
                Verification.date >= recent_date
            )
        ).order_by(desc(Verification.date))
        
        recent_verifications = (await self.session.execute(stmt)).scalars().all()
        
        total_verifications = len(recent_verifications)
        compliance_issues = 0
        critical_issues = 0
        
        for verification in recent_verifications:
            # Run existing compliance rules
            flags = await run_verification_rules(self.session, verification)
            if flags:
                compliance_issues += 1
                if any(f.severity == 'error' for f in flags):
                    critical_issues += 1
        
        compliance_rate = ((total_verifications - compliance_issues) / max(1, total_verifications)) * 100
        
        # Health status
        if compliance_rate >= 95 and critical_issues == 0:
            health_status = "EXCELLENT"
        elif compliance_rate >= 85 and critical_issues <= 1:
            health_status = "GOOD" 
        elif compliance_rate >= 70:
            health_status = "WARNING"
        else:
            health_status = "CRITICAL"
        
        return {
            "period": f"Last 7 days",
            "total_verifications": total_verifications,
            "compliance_rate": f"{compliance_rate:.1f}%",
            "compliance_issues": compliance_issues,
            "critical_issues": critical_issues,
            "health_status": health_status,
            "next_vat_deadline": self._get_next_vat_deadline(),
            "recommendations": self._get_daily_recommendations(health_status)
        }
    
    def _get_next_vat_deadline(self) -> str:
        """Get next VAT reporting deadline."""
        today = date.today()
        
        # VAT returns due 12th of next month
        next_month = today.replace(day=1) + timedelta(days=32)
        vat_deadline = next_month.replace(day=12)
        
        days_until = (vat_deadline - today).days
        return f"{vat_deadline.isoformat()} ({days_until} days)"
    
    def _get_daily_recommendations(self, health_status: str) -> List[str]:
        """Daily recommendations based on compliance health."""
        
        recommendations = [
            "Granska dagens transaktioner för fullständighet",
            "Kontrollera att alla kvitton är arkiverade"
        ]
        
        if health_status in ["WARNING", "CRITICAL"]:
            recommendations.extend([
                "Åtgärda flaggade compliance-problem omedelbart",
                "Genomför månadsvis compliance-genomgång",
                "Överväg utbildning i svensk bokföringslag"
            ])
        
        return recommendations


async def check_pre_verification_compliance(session: AsyncSession, org_id: int, verification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for pre-verification compliance check."""
    guardian = ComplianceGuardian(session, org_id)
    return await guardian.pre_verification_check(verification_data)


async def daily_compliance_report(session: AsyncSession, org_id: int) -> Dict[str, Any]:
    """Generate daily compliance monitoring report."""
    guardian = ComplianceGuardian(session, org_id)
    return await guardian.daily_compliance_monitoring()