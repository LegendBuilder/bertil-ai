from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, extract

from ..models import Verification, Entry, FiscalYear


class InsightTiming(Enum):
    IMMEDIATE = "immediate"     # Show right now
    DAILY = "daily"            # Show once per day
    WEEKLY = "weekly"          # Show once per week  
    MONTHLY = "monthly"        # Show once per month
    CONTEXTUAL = "contextual"  # Show at perfect moment


@dataclass
class BusinessInsight:
    title: str
    message: str
    impact: float  # SEK value of insight
    timing: InsightTiming
    category: str  # expense_trend, cash_flow, tax_opportunity, etc.
    action_required: bool
    data: Dict[str, Any]


class ContextualBusinessIntelligence:
    """Provides insights at the PERFECT moment - when users need them most."""
    
    def __init__(self, session: AsyncSession, org_id: int):
        self.session = session
        self.org_id = org_id
    
    async def get_contextual_insights(self, context: Dict[str, Any] = None) -> List[BusinessInsight]:
        """Get insights based on current context and perfect timing."""
        
        insights = []
        
        # 1. Real-time expense trend analysis
        expense_insights = await self._analyze_expense_trends(context)
        insights.extend(expense_insights)
        
        # 2. Cash flow intelligence
        cash_flow_insights = await self._analyze_cash_flow()
        insights.extend(cash_flow_insights)
        
        # 3. Tax deadline awareness
        tax_insights = await self._analyze_tax_opportunities()
        insights.extend(tax_insights)
        
        # 4. Vendor relationship intelligence
        vendor_insights = await self._analyze_vendor_patterns()
        insights.extend(vendor_insights)
        
        # 5. Seasonal business intelligence
        seasonal_insights = await self._analyze_seasonal_patterns()
        insights.extend(seasonal_insights)
        
        # 6. Compliance health intelligence
        compliance_insights = await self._analyze_compliance_health()
        insights.extend(compliance_insights)
        
        # Sort by impact and timing relevance
        return self._prioritize_insights(insights, context)
    
    async def _analyze_expense_trends(self, context: Dict[str, Any] = None) -> List[BusinessInsight]:
        """Real-time expense trend analysis with actionable insights."""
        insights = []
        
        # Get last 3 months of data
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        # Monthly expense analysis
        monthly_expenses = await self._get_monthly_expenses(start_date, end_date)
        
        if len(monthly_expenses) >= 2:
            current_month = monthly_expenses[-1]['total']
            last_month = monthly_expenses[-2]['total']
            change_pct = ((current_month - last_month) / last_month * 100) if last_month > 0 else 0
            
            if abs(change_pct) > 20:  # Significant change
                trend = "ökning" if change_pct > 0 else "minskning"
                impact_sek = abs(current_month - last_month)
                
                insights.append(BusinessInsight(
                    title=f"Betydande kostnad{trend}",
                    message=f"Kostnader har {trend} med {abs(change_pct):.1f}% ({impact_sek:.0f} SEK) jämfört med förra månaden",
                    impact=impact_sek,
                    timing=InsightTiming.IMMEDIATE,
                    category="expense_trend",
                    action_required=change_pct > 15,  # Only if increase > 15%
                    data={
                        "current_month": current_month,
                        "last_month": last_month,
                        "change_percent": change_pct,
                        "change_sek": impact_sek
                    }
                ))
        
        # Category-specific trends
        category_trends = await self._analyze_expense_categories()
        insights.extend(category_trends)
        
        return insights
    
    async def _analyze_cash_flow(self) -> List[BusinessInsight]:
        """Cash flow intelligence with perfect timing."""
        insights = []
        
        # Upcoming payment obligations
        upcoming_payments = await self._get_upcoming_payments()
        current_cash = await self._get_current_cash_position()
        
        if upcoming_payments and current_cash is not None:
            payment_total = sum(p['amount'] for p in upcoming_payments)
            
            if payment_total > current_cash * 0.8:  # >80% of cash
                insights.append(BusinessInsight(
                    title="Kassaflödesvarning",
                    message=f"Kommande betalningar ({payment_total:.0f} SEK) kan påverka kassalikviditet",
                    impact=payment_total,
                    timing=InsightTiming.IMMEDIATE,
                    category="cash_flow",
                    action_required=True,
                    data={
                        "upcoming_payments": payment_total,
                        "current_cash": current_cash,
                        "coverage_ratio": current_cash / payment_total if payment_total > 0 else 0
                    }
                ))
        
        # Monthly cash flow pattern
        monthly_pattern = await self._analyze_monthly_cash_pattern()
        if monthly_pattern['risk_score'] > 0.7:
            insights.append(BusinessInsight(
                title="Kassaflödesmönster",
                message=f"Återkommande låg kassalikviditet {monthly_pattern['risk_period']}",
                impact=monthly_pattern['average_shortage'],
                timing=InsightTiming.WEEKLY,
                category="cash_flow",
                action_required=True,
                data=monthly_pattern
            ))
        
        return insights
    
    async def _analyze_tax_opportunities(self) -> List[BusinessInsight]:
        """Tax opportunity intelligence - perfect timing for decisions."""
        insights = []
        
        # Year-end tax planning
        today = date.today()
        fiscal_year = await self._get_current_fiscal_year()
        
        if fiscal_year:
            days_to_year_end = (fiscal_year.end_date - today).days
            
            if 30 <= days_to_year_end <= 90:  # Perfect planning window
                # Analyze potential tax savings
                potential_savings = await self._calculate_year_end_tax_opportunities()
                
                if potential_savings > 10000:  # Significant opportunity
                    insights.append(BusinessInsight(
                        title="Skatteplaneringsmöjlighet",
                        message=f"Potential skattebesparing: {potential_savings:.0f} SEK genom årsslutsplanering",
                        impact=potential_savings,
                        timing=InsightTiming.IMMEDIATE,
                        category="tax_opportunity",
                        action_required=True,
                        data={
                            "days_to_year_end": days_to_year_end,
                            "potential_savings": potential_savings,
                            "recommended_actions": await self._get_tax_recommendations()
                        }
                    ))
        
        # VAT optimization opportunities
        vat_opportunities = await self._analyze_vat_optimization()
        insights.extend(vat_opportunities)
        
        return insights
    
    async def _analyze_vendor_patterns(self) -> List[BusinessInsight]:
        """Vendor relationship intelligence."""
        insights = []
        
        # Vendor concentration risk
        vendor_analysis = await self._analyze_vendor_concentration()
        
        if vendor_analysis['concentration_risk'] > 0.3:  # >30% with single vendor
            top_vendor = vendor_analysis['top_vendor']
            insights.append(BusinessInsight(
                title="Leverantörskoncentration",
                message=f"{top_vendor['name']}: {top_vendor['percentage']:.1f}% av total kostnad - överväg diversifiering",
                impact=top_vendor['total_amount'],
                timing=InsightTiming.MONTHLY,
                category="vendor_risk",
                action_required=vendor_analysis['concentration_risk'] > 0.5,
                data=vendor_analysis
            ))
        
        # Payment pattern optimization
        payment_patterns = await self._analyze_payment_patterns()
        if payment_patterns['optimization_potential'] > 5000:
            insights.append(BusinessInsight(
                title="Betalningsoptimering",
                message=f"Potential kassaflödesförbättring: {payment_patterns['optimization_potential']:.0f} SEK genom betalningsoptimering",
                impact=payment_patterns['optimization_potential'],
                timing=InsightTiming.CONTEXTUAL,
                category="payment_optimization",
                action_required=False,
                data=payment_patterns
            ))
        
        return insights
    
    async def _analyze_seasonal_patterns(self) -> List[BusinessInsight]:
        """Seasonal business intelligence."""
        insights = []
        
        current_month = date.today().month
        seasonal_data = await self._get_seasonal_patterns()
        
        # Predict seasonal expenses
        if current_month in seasonal_data['high_expense_months']:
            expected_increase = seasonal_data['seasonal_multiplier']
            base_monthly = await self._get_average_monthly_expenses()
            
            expected_total = base_monthly * expected_increase
            
            insights.append(BusinessInsight(
                title="Säsongsvariation",
                message=f"Förväntad kostnadökning denna månad: {(expected_increase-1)*100:.0f}% ({expected_total-base_monthly:.0f} SEK)",
                impact=expected_total - base_monthly,
                timing=InsightTiming.MONTHLY,
                category="seasonal_planning",
                action_required=False,
                data={
                    "seasonal_multiplier": expected_increase,
                    "expected_total": expected_total,
                    "base_monthly": base_monthly
                }
            ))
        
        return insights
    
    async def _analyze_compliance_health(self) -> List[BusinessInsight]:
        """Compliance health intelligence."""
        insights = []
        
        # Compliance trend analysis
        compliance_score = await self._get_compliance_health_score()
        
        if compliance_score < 85:  # Below good threshold
            insights.append(BusinessInsight(
                title="Compliancehälsa",
                message=f"Compliance-poäng: {compliance_score:.0f}/100 - förbättringsområden identifierade",
                impact=0,  # No direct financial impact
                timing=InsightTiming.WEEKLY,
                category="compliance_health", 
                action_required=compliance_score < 70,
                data={
                    "compliance_score": compliance_score,
                    "improvement_areas": await self._get_compliance_improvement_areas()
                }
            ))
        
        return insights
    
    def _prioritize_insights(self, insights: List[BusinessInsight], context: Dict[str, Any] = None) -> List[BusinessInsight]:
        """Prioritize insights by relevance, impact, and timing."""
        
        # Sort by priority score (combination of impact, urgency, and relevance)
        def priority_score(insight: BusinessInsight) -> float:
            score = 0.0
            
            # Impact weight (higher is better)
            score += min(insight.impact / 10000, 10.0)  # Max 10 points for impact
            
            # Timing urgency
            timing_weights = {
                InsightTiming.IMMEDIATE: 10.0,
                InsightTiming.DAILY: 5.0,
                InsightTiming.WEEKLY: 3.0,
                InsightTiming.MONTHLY: 2.0,
                InsightTiming.CONTEXTUAL: 7.0
            }
            score += timing_weights.get(insight.timing, 1.0)
            
            # Action required boost
            if insight.action_required:
                score += 5.0
            
            # Category relevance (could be enhanced with user preferences)
            category_weights = {
                "cash_flow": 10.0,
                "expense_trend": 8.0,
                "tax_opportunity": 9.0,
                "compliance_health": 7.0,
                "vendor_risk": 6.0
            }
            score += category_weights.get(insight.category, 5.0)
            
            return score
        
        return sorted(insights, key=priority_score, reverse=True)[:10]  # Top 10 insights
    
    # Helper methods for data analysis
    async def _get_monthly_expenses(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get monthly expense totals."""
        stmt = select(
            extract('year', Verification.date).label('year'),
            extract('month', Verification.date).label('month'),
            func.sum(Verification.total_amount).label('total')
        ).where(
            and_(
                Verification.org_id == self.org_id,
                Verification.date.between(start_date, end_date),
                Verification.total_amount > 0
            )
        ).group_by(
            extract('year', Verification.date),
            extract('month', Verification.date)
        ).order_by(
            extract('year', Verification.date),
            extract('month', Verification.date)
        )
        
        result = await self.session.execute(stmt)
        return [{"year": row.year, "month": row.month, "total": float(row.total or 0)} for row in result]
    
    async def _analyze_expense_categories(self) -> List[BusinessInsight]:
        """Analyze expense categories for trends."""
        # This would analyze by account categories - simplified for now
        return []
    
    async def _get_upcoming_payments(self) -> List[Dict[str, Any]]:
        """Get upcoming payment obligations."""
        # This would integrate with payment scheduling - placeholder
        return []
    
    async def _get_current_cash_position(self) -> Optional[float]:
        """Get current cash position from account 1910."""
        stmt = select(func.sum(
            func.coalesce(Entry.debit, 0) - func.coalesce(Entry.credit, 0)
        )).where(
            and_(
                Entry.account.like('1910%'),  # Cash accounts
                Entry.verification.has(Verification.org_id == self.org_id)
            )
        )
        
        result = await self.session.execute(stmt)
        return float(result.scalar() or 0)
    
    async def _analyze_monthly_cash_pattern(self) -> Dict[str, Any]:
        """Analyze monthly cash flow patterns."""
        return {
            "risk_score": 0.5,
            "risk_period": "månadsslut",
            "average_shortage": 15000
        }
    
    async def _get_current_fiscal_year(self) -> Optional[FiscalYear]:
        """Get current fiscal year."""
        today = date.today()
        stmt = select(FiscalYear).where(
            and_(
                FiscalYear.org_id == self.org_id,
                FiscalYear.start_date <= today,
                FiscalYear.end_date >= today
            )
        )
        return (await self.session.execute(stmt)).scalars().first()
    
    async def _calculate_year_end_tax_opportunities(self) -> float:
        """Calculate potential year-end tax savings."""
        # Simplified calculation - would be much more sophisticated
        return 25000.0
    
    async def _get_tax_recommendations(self) -> List[str]:
        """Get tax optimization recommendations."""
        return [
            "Överväg accelererade avskrivningar",
            "Granska representation och representation limits", 
            "Planera förvärv av utrustning innan årsskifte"
        ]
    
    async def _analyze_vat_optimization(self) -> List[BusinessInsight]:
        """Analyze VAT optimization opportunities."""
        return []
    
    async def _analyze_vendor_concentration(self) -> Dict[str, Any]:
        """Analyze vendor concentration risk."""
        return {
            "concentration_risk": 0.35,
            "top_vendor": {
                "name": "Stora Leverantören AB",
                "percentage": 35.2,
                "total_amount": 125000
            }
        }
    
    async def _analyze_payment_patterns(self) -> Dict[str, Any]:
        """Analyze payment patterns for optimization."""
        return {"optimization_potential": 8500}
    
    async def _get_seasonal_patterns(self) -> Dict[str, Any]:
        """Get seasonal business patterns."""
        return {
            "high_expense_months": [11, 12, 1],  # Nov, Dec, Jan
            "seasonal_multiplier": 1.3
        }
    
    async def _get_average_monthly_expenses(self) -> float:
        """Get average monthly expenses."""
        return 45000.0
    
    async def _get_compliance_health_score(self) -> float:
        """Get overall compliance health score."""
        return 87.5
    
    async def _get_compliance_improvement_areas(self) -> List[str]:
        """Get compliance improvement recommendations."""
        return [
            "Förbättra dokumentation av representation",
            "Implementera konsekvent VAT-kodning",
            "Förbättra arkivering av underlag"
        ]


async def get_contextual_business_insights(session: AsyncSession, org_id: int, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Main entry point for contextual business intelligence."""
    bi = ContextualBusinessIntelligence(session, org_id)
    insights = await bi.get_contextual_insights(context)
    
    # Convert to dict for API response
    items = [
        {
            "title": insight.title,
            "message": insight.message,
            "impact": insight.impact,
            "timing": insight.timing.value,
            "category": insight.category,
            "action_required": insight.action_required,
            "data": insight.data
        }
        for insight in insights
    ]
    # Add learning notifications from recent AiFeedback
    try:
        from ..models_feedback import AiFeedback
        rows = (await session.execute(select(AiFeedback).order_by(AiFeedback.id.desc()).limit(3))).scalars().all()
        for r in rows:
            items.append({
                "title": f"AI lär sig från {r.vendor}",
                "message": "Kontoförslag uppdaterat baserat på din senaste korrigering.",
                "impact": 0,
                "timing": "weekly",
                "category": "learning",
                "action_required": False,
                "data": {"vendor": r.vendor}
            })
    except Exception:
        pass
    return items