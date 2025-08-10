from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Tuple
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ..models import Verification, Entry, FiscalYear


class ProactiveTaxOptimizer:
    """REAL Swedish tax optimization - automatically optimizes deductions and timing."""
    
    def __init__(self, session: AsyncSession, org_id: int):
        self.session = session
        self.org_id = org_id
        
        # Swedish tax rules 2025
        self.REPRESENTATION_LIMIT = 0.5  # 50% deductible
        self.COMPANY_CAR_BENEFIT_RATE = 0.10  # 10% of car value
        self.MEAL_DEDUCTION_MAX = 120  # SEK per meal
        self.TRAVEL_DEDUCTION_RATES = {
            'km_car': 1.85,  # SEK per km for car
            'km_bike': 0.50,  # SEK per km for bike
            'meal_away': 280,  # SEK per day away from home
        }
        
    async def optimize_verification(self, verification_id: int) -> Dict[str, Any]:
        """Optimize a single verification for tax efficiency."""
        
        # Get verification and entries
        stmt = select(Verification).where(Verification.id == verification_id)
        verification = (await self.session.execute(stmt)).scalars().first()
        
        if not verification:
            return {"error": "Verification not found"}
            
        entries = await self._get_entries(verification_id)
        
        optimizations = []
        total_savings = 0.0
        
        # 1. Representation optimization (50% rule)
        rep_optimization = await self._optimize_representation(verification, entries)
        if rep_optimization['savings'] > 0:
            optimizations.append(rep_optimization)
            total_savings += rep_optimization['savings']
            
        # 2. Travel expense optimization 
        travel_optimization = await self._optimize_travel_expenses(verification, entries)
        if travel_optimization['savings'] > 0:
            optimizations.append(travel_optimization)
            total_savings += travel_optimization['savings']
            
        # 3. Timing optimization (year-end planning)
        timing_optimization = await self._optimize_timing(verification)
        if timing_optimization['savings'] > 0:
            optimizations.append(timing_optimization)
            total_savings += timing_optimization['savings']
            
        # 4. Account classification optimization
        classification_optimization = await self._optimize_account_classification(verification, entries)
        if classification_optimization['savings'] > 0:
            optimizations.append(classification_optimization)
            total_savings += classification_optimization['savings']
            
        return {
            "verification_id": verification_id,
            "optimizations": optimizations,
            "total_tax_savings": round(total_savings, 2),
            "status": "optimized" if optimizations else "no_optimizations_needed"
        }
    
    async def _optimize_representation(self, verification: Verification, entries: List[Entry]) -> Dict[str, Any]:
        """Apply Swedish representation rules (50% deductible)."""
        
        vendor = (verification.counterparty or "").lower()
        total_amount = float(verification.total_amount or 0)
        
        # Detect representation expenses
        representation_keywords = [
            'restaurang', 'café', 'lunch', 'middag', 'fika', 'bar', 'pub',
            'hotell', 'konferens', 'meeting', 'representation'
        ]
        
        is_representation = any(keyword in vendor for keyword in representation_keywords)
        
        if not is_representation or total_amount <= 0:
            return {"type": "representation", "savings": 0.0, "reason": "Not representation expense"}
            
        # Check if already using representation account (5810-5819)
        using_rep_account = any(str(e.account).startswith('581') for e in entries)
        
        if using_rep_account:
            return {"type": "representation", "savings": 0.0, "reason": "Already optimized"}
            
        # Calculate tax saving: 50% of amount is deductible 
        # Corporate tax rate 20.6% in Sweden
        tax_savings = total_amount * 0.50 * 0.206
        
        return {
            "type": "representation",
            "savings": round(tax_savings, 2),
            "reason": f"Move to account 5811 (Representation) - 50% deductible rule",
            "suggested_account": "5811",
            "current_accounts": [str(e.account) for e in entries if e.debit and e.debit > 0],
            "rule": "Bokföringslagen 4 kap 2§ + Skatteverket representation rules"
        }
    
    async def _optimize_travel_expenses(self, verification: Verification, entries: List[Entry]) -> Dict[str, Any]:
        """Optimize travel expenses with Swedish mileage rates."""
        
        vendor = (verification.counterparty or "").lower()
        total_amount = float(verification.total_amount or 0)
        
        # Detect travel expenses
        travel_keywords = ['taxi', 'uber', 'transport', 'tåg', 'flyg', 'bensin', 'parkering']
        
        is_travel = any(keyword in vendor for keyword in travel_keywords)
        
        if not is_travel:
            return {"type": "travel", "savings": 0.0, "reason": "Not travel expense"}
            
        # Check if using optimal travel account
        optimal_accounts = ['5611', '5612', '5613']  # Travel accounts
        using_optimal = any(str(e.account) in optimal_accounts for e in entries)
        
        if using_optimal:
            return {"type": "travel", "savings": 0.0, "reason": "Already optimized"}
            
        # For taxi/transport: suggest 5611 (Business travel)
        # VAT treatment: 6% for public transport, 25% for taxi
        suggested_account = "5611"
        vat_optimization = ""
        
        if 'taxi' in vendor or 'uber' in vendor:
            # Taxi should be 6% VAT in Sweden for business travel
            current_vat_rate = self._get_current_vat_rate(entries, total_amount)
            if current_vat_rate > 0.06:
                vat_savings = total_amount * (current_vat_rate - 0.06)
                vat_optimization = f" + VAT optimization: {vat_savings:.2f} SEK saved by using 6% rate"
        
        # Base tax saving from proper categorization
        tax_savings = total_amount * 0.206  # Full deductible vs potentially non-deductible
        
        return {
            "type": "travel",  
            "savings": round(tax_savings, 2),
            "reason": f"Move to account {suggested_account} (Business travel){vat_optimization}",
            "suggested_account": suggested_account,
            "vat_code": "SE06" if 'taxi' in vendor else "SE25",
            "rule": "Inkomstskattelagen 16 kap - Resor i tjänsten"
        }
    
    async def _optimize_timing(self, verification: Verification) -> Dict[str, Any]:
        """Year-end timing optimization."""
        
        if not verification.date:
            return {"type": "timing", "savings": 0.0, "reason": "No date"}
            
        # Get fiscal year
        stmt = select(FiscalYear).where(
            FiscalYear.org_id == self.org_id,
            FiscalYear.start_date <= verification.date,
            FiscalYear.end_date >= verification.date
        )
        fiscal_year = (await self.session.execute(stmt)).scalars().first()
        
        if not fiscal_year:
            return {"type": "timing", "savings": 0.0, "reason": "No fiscal year defined"}
            
        # Check if near year-end (last 60 days)
        days_to_year_end = (fiscal_year.end_date - verification.date).days
        
        if days_to_year_end > 60:
            return {"type": "timing", "savings": 0.0, "reason": "Not near year-end"}
            
        # For expenses: accelerate if profitable year
        # For income: delay if possible
        
        total_amount = float(verification.total_amount or 0)
        
        # Simple optimization: if major expense near year-end, suggest acceleration
        if total_amount > 10000:  # Major expense
            tax_savings = total_amount * 0.206  # Corporate tax rate
            
            return {
                "type": "timing",
                "savings": round(tax_savings, 2),
                "reason": f"Accelerate major expense ({days_to_year_end} days to year-end)",
                "suggestion": "Consider pre-paying or accelerating this expense for current tax year",
                "rule": "Inkomstskattelagen - Periodiseringsregler"
            }
            
        return {"type": "timing", "savings": 0.0, "reason": "No timing optimization available"}
    
    async def _optimize_account_classification(self, verification: Verification, entries: List[Entry]) -> Dict[str, Any]:
        """Optimize account classification for better tax treatment."""
        
        vendor = (verification.counterparty or "").lower()
        total_amount = float(verification.total_amount or 0)
        
        # Check for R&D expenses (eligible for additional deductions)
        rd_keywords = ['utveckling', 'forskning', 'konsult', 'expert', 'system', 'software', 'teknik']
        
        is_rd = any(keyword in vendor for keyword in rd_keywords)
        
        if is_rd and total_amount > 1000:
            # Check if using R&D account
            using_rd_account = any(str(e.account).startswith('761') for e in entries)  # R&D costs
            
            if not using_rd_account:
                # R&D gets enhanced deductions in Sweden
                enhanced_deduction = total_amount * 0.20  # 20% additional deduction
                tax_savings = enhanced_deduction * 0.206
                
                return {
                    "type": "classification",
                    "savings": round(tax_savings, 2),
                    "reason": "Move to R&D account for enhanced deductions",
                    "suggested_account": "7610",  # Research & Development
                    "rule": "Inkomstskattelagen - FoU-avdrag"
                }
        
        return {"type": "classification", "savings": 0.0, "reason": "No classification optimization"}
    
    def _get_current_vat_rate(self, entries: List[Entry], total_amount: float) -> float:
        """Calculate current VAT rate from entries."""
        if total_amount <= 0:
            return 0.0
            
        # Find VAT entry (account 2641)
        vat_amount = 0.0
        for entry in entries:
            if str(entry.account).startswith('2641') and entry.debit:
                vat_amount += float(entry.debit)
                
        if vat_amount <= 0:
            return 0.0
            
        # Calculate rate: VAT / (Total - VAT) 
        net_amount = total_amount - vat_amount
        return vat_amount / net_amount if net_amount > 0 else 0.0
    
    async def _get_entries(self, verification_id: int) -> List[Entry]:
        """Get all entries for a verification."""
        stmt = select(Entry).where(Entry.verification_id == verification_id)
        return list((await self.session.execute(stmt)).scalars().all())
    
    async def monthly_tax_optimization_report(self) -> Dict[str, Any]:
        """Generate monthly tax optimization opportunities."""
        
        # Get current month's verifications
        today = date.today()
        start_of_month = today.replace(day=1)
        
        stmt = select(Verification).where(
            and_(
                Verification.org_id == self.org_id,
                Verification.date >= start_of_month,
                Verification.date <= today
            )
        )
        
        verifications = (await self.session.execute(stmt)).scalars().all()
        
        total_potential_savings = 0.0
        optimization_count = 0
        
        for verification in verifications:
            result = await self.optimize_verification(verification.id)
            if result.get('total_tax_savings', 0) > 0:
                total_potential_savings += result['total_tax_savings']
                optimization_count += 1
        
        return {
            "period": f"{start_of_month} to {today}",
            "total_potential_savings": round(total_potential_savings, 2),
            "optimizations_available": optimization_count,
            "total_verifications": len(verifications),
            "optimization_rate": f"{(optimization_count/max(1, len(verifications))*100):.1f}%"
        }


async def optimize_verification_taxes(session: AsyncSession, org_id: int, verification_id: int) -> Dict[str, Any]:
    """Main entry point for tax optimization."""
    optimizer = ProactiveTaxOptimizer(session, org_id)
    return await optimizer.optimize_verification(verification_id)


async def generate_tax_optimization_report(session: AsyncSession, org_id: int) -> Dict[str, Any]:
    """Generate tax optimization report."""
    optimizer = ProactiveTaxOptimizer(session, org_id)
    return await optimizer.monthly_tax_optimization_report()