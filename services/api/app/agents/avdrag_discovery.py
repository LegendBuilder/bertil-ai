"""
Swedish Tax Deduction Discovery Engine

This module discovers all possible tax deductions and benefits from receipts,
transactions, and user data. It implements the complete Swedish tax code
to maximize user benefits.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..config import settings


@dataclass
class AvdragOpportunity:
    """Represents a discovered tax deduction opportunity"""
    category: str
    deduction_type: str
    amount: float
    max_annual_limit: Optional[float]
    confidence: float
    description: str
    requirements: List[str]
    supporting_documents: List[str]
    tax_savings_estimate: float


class SwedishTaxRuleEngine:
    """
    Comprehensive Swedish tax rule engine that discovers all possible
    deductions and optimizations from user financial data.
    """
    
    def __init__(self):
        self.rules = self._load_tax_rules()
        self.current_year = datetime.now().year
        
    def _load_tax_rules(self) -> Dict[str, Any]:
        """Load comprehensive Swedish tax rules from knowledge base"""
        # Get absolute path to project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        kb_path = project_root / "kb" / "personal"
        
        rules = {}
        
        # Load all rule files
        rule_files = [
            "comprehensive_avdrag_rules.json",
            "pension_optimization_rules.json"
        ]
        
        for rule_file in rule_files:
            file_path = kb_path / rule_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for snippet in data.get('snippets', []):
                        category = snippet.get('category', '')
                        rules[category] = snippet.get('rules', {})
        
        return rules
    
    async def analyze_receipt(self, receipt_data: dict, user_profile: dict) -> List[AvdragOpportunity]:
        """
        Analyze a receipt/transaction for all possible tax deductions
        
        Args:
            receipt_data: Extracted receipt information (vendor, amount, date, category)
            user_profile: User information (income, family status, work situation)
            
        Returns:
            List of discovered deduction opportunities
        """
        opportunities = []
        
        vendor = receipt_data.get('vendor', '').lower()
        amount = float(receipt_data.get('total', 0))
        date_str = receipt_data.get('date', '')
        category = receipt_data.get('category', '').lower()
        description = receipt_data.get('description', '').lower()
        
        # ROT/RUT Deduction Analysis
        rot_rut_opportunities = await self._analyze_rot_rut(
            vendor, amount, description, user_profile
        )
        opportunities.extend(rot_rut_opportunities)
        
        # Work Equipment Analysis
        work_opportunities = await self._analyze_work_equipment(
            vendor, amount, description, user_profile
        )
        opportunities.extend(work_opportunities)
        
        # Medical Expense Analysis
        medical_opportunities = await self._analyze_medical_expenses(
            vendor, amount, description, user_profile
        )
        opportunities.extend(medical_opportunities)
        
        # Travel/Commute Analysis
        travel_opportunities = await self._analyze_travel_expenses(
            vendor, amount, description, user_profile
        )
        opportunities.extend(travel_opportunities)
        
        # Education/Training Analysis
        education_opportunities = await self._analyze_education_expenses(
            vendor, amount, description, user_profile
        )
        opportunities.extend(education_opportunities)
        
        # Charity Donation Analysis
        charity_opportunities = await self._analyze_charitable_donations(
            vendor, amount, description, user_profile
        )
        opportunities.extend(charity_opportunities)
        
        # Union/Professional Fee Analysis
        union_opportunities = await self._analyze_union_fees(
            vendor, amount, description, user_profile
        )
        opportunities.extend(union_opportunities)
        
        return opportunities
    
    async def _analyze_rot_rut(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for ROT/RUT home service deductions"""
        opportunities = []
        
        rot_rules = self.rules.get("ROT Deductions (Home Renovation)", {}).get("rot_deduction", {})
        rut_rules = self.rules.get("RUT Deductions (Home Services)", {}).get("rut_deduction", {})
        
        # ROT Detection (Home Renovation)
        rot_keywords = [
            'målare', 'elektriker', 'rörmokare', 'snickare', 'kakel', 'golv',
            'kök', 'badrum', 'tak', 'isolation', 'värmepump', 'fönster', 'dörr',
            'painter', 'electrician', 'plumber', 'carpenter', 'tiles', 'flooring',
            'kitchen', 'bathroom', 'roof', 'insulation', 'heat pump', 'window', 'door'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in rot_keywords):
            max_deduction = rot_rules.get("max_annual_deduction", 75000)
            deduction_rate = rot_rules.get("deduction_rate", 0.30)
            potential_deduction = amount * deduction_rate
            
            opportunities.append(AvdragOpportunity(
                category="ROT",
                deduction_type="home_renovation",
                amount=potential_deduction,
                max_annual_limit=max_deduction,
                confidence=0.85,
                description=f"ROT-avdrag för hemrenovering: {deduction_rate*100}% av arbetskostnad",
                requirements=[
                    "Arbete utfört på egen bostad",
                    "Elektronisk betalning krävs",
                    "Endast arbetskostnad (ej material)",
                    "Entreprenör måste vara registrerad"
                ],
                supporting_documents=["receipt", "invoice", "payment_proof"],
                tax_savings_estimate=potential_deduction
            ))
        
        # RUT Detection (Home Services)
        rut_keywords = [
            'städning', 'fönsterputs', 'tvätt', 'strykning', 'trädgård', 'gräs',
            'snöröjning', 'flytt', 'dator', 'it-hjälp', 'häck',
            'cleaning', 'window', 'laundry', 'ironing', 'garden', 'grass',
            'snow', 'moving', 'computer', 'it-help', 'hedge'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in rut_keywords):
            max_deduction = rut_rules.get("max_annual_deduction", 75000)
            deduction_rate = rut_rules.get("deduction_rate", 0.50)
            potential_deduction = amount * deduction_rate
            
            opportunities.append(AvdragOpportunity(
                category="RUT",
                deduction_type="home_services",
                amount=potential_deduction,
                max_annual_limit=max_deduction,
                confidence=0.90,
                description=f"RUT-avdrag för hemtjänster: {deduction_rate*100}% av kostnad",
                requirements=[
                    "Tjänster utförda i hemmet eller närområdet",
                    "Elektronisk betalning krävs",
                    "Entreprenör måste vara F-skattregistrerad"
                ],
                supporting_documents=["receipt", "payment_proof"],
                tax_savings_estimate=potential_deduction
            ))
        
        return opportunities
    
    async def _analyze_work_equipment(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for work equipment and protective clothing deductions"""
        opportunities = []
        
        work_rules = self.rules.get("Work Equipment and Protective Clothing", {})
        
        # Protective equipment keywords
        protective_keywords = [
            'hjälm', 'skyddsglasögon', 'hörselskydd', 'säkerhetsskor', 'stålhätta',
            'skyddshandskar', 'reflexväst', 'varselkläder', 'andningsskydd',
            'helmet', 'safety glasses', 'hearing protection', 'safety boots', 'steel toe',
            'work gloves', 'reflective vest', 'hi-vis', 'respirator'
        ]
        
        # Work tools keywords  
        tool_keywords = [
            'verktyg', 'hammare', 'skruvmejsel', 'arbetskläder', 'uniform',
            'professionell mjukvara', 'facklitteratur', 'instrument',
            'tools', 'hammer', 'screwdriver', 'work clothes', 'uniform',
            'professional software', 'trade books', 'instruments'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in protective_keywords + tool_keywords):
            opportunities.append(AvdragOpportunity(
                category="Work Equipment",
                deduction_type="full_cost",
                amount=amount,
                max_annual_limit=None,
                confidence=0.75,
                description="Avdrag för arbetsutrustning och skyddskläder",
                requirements=[
                    "Används endast för arbete",
                    "Krävs av arbetsgivare eller lag",
                    "Ersätts ej av arbetsgivare"
                ],
                supporting_documents=["receipt", "employer_requirement_proof"],
                tax_savings_estimate=amount * 0.32  # Approximate tax rate
            ))
        
        return opportunities
    
    async def _analyze_medical_expenses(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for medical expense deductions"""
        opportunities = []
        
        medical_rules = self.rules.get("Medical Expense Deductions", {}).get("medical_expenses", {})
        threshold = medical_rules.get("threshold", 5000)
        
        medical_keywords = [
            'apotek', 'sjukhus', 'vårdcentral', 'läkare', 'tandläkare', 'fysioterapi',
            'medicin', 'glasögon', 'linser', 'hörapparat', 'ortoped',
            'pharmacy', 'hospital', 'clinic', 'doctor', 'dentist', 'physiotherapy',
            'medicine', 'glasses', 'contacts', 'hearing aid', 'orthopedic'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in medical_keywords):
            # Medical expenses are only deductible above SEK 5,000 threshold
            current_year_total = user_profile.get('medical_expenses_ytd', 0) + amount
            
            if current_year_total > threshold:
                deductible_amount = min(amount, current_year_total - threshold)
                
                opportunities.append(AvdragOpportunity(
                    category="Medical Expenses",
                    deduction_type="above_threshold",
                    amount=deductible_amount,
                    max_annual_limit=None,
                    confidence=0.80,
                    description=f"Sjukvårdsavdrag för kostnader över {threshold} SEK",
                    requirements=[
                        f"Totala sjukvårdskostnader över {threshold} SEK per år",
                        "Medicinskt nödvändiga kostnader",
                        "Ej ersatta av försäkring"
                    ],
                    supporting_documents=["medical_receipt", "prescription", "referral"],
                    tax_savings_estimate=deductible_amount * 0.32
                ))
        
        return opportunities
    
    async def _analyze_travel_expenses(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for travel and commute deductions"""
        opportunities = []
        
        travel_rules = self.rules.get("Travel and Commute Deductions", {})
        
        # Check for commute-related expenses
        travel_keywords = [
            'bensin', 'diesel', 'parkering', 'bro', 'färja', 'tåg', 'buss',
            'gasoline', 'fuel', 'parking', 'bridge', 'ferry', 'train', 'bus'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in travel_keywords):
            # This would need more context about user's commute distance and pattern
            work_distance = user_profile.get('work_commute_km', 0)
            
            if work_distance > 50:  # Minimum distance requirement
                opportunities.append(AvdragOpportunity(
                    category="Travel Expenses",
                    deduction_type="commute_related",
                    amount=amount,
                    max_annual_limit=None,
                    confidence=0.60,  # Lower confidence without more context
                    description="Möjligt reseavdrag för arbetsresor",
                    requirements=[
                        "Resa till/från arbete",
                        "Total resväg >50km", 
                        "Nödvändig för arbetet"
                    ],
                    supporting_documents=["receipt", "employment_verification", "distance_proof"],
                    tax_savings_estimate=amount * 0.32
                ))
        
        return opportunities
    
    async def _analyze_education_expenses(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for education and training deductions"""
        opportunities = []
        
        education_keywords = [
            'kurs', 'utbildning', 'certifiering', 'konferens', 'seminarium', 'bok', 'litteratur',
            'course', 'education', 'certification', 'conference', 'seminar', 'book', 'literature'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in education_keywords):
            opportunities.append(AvdragOpportunity(
                category="Education",
                deduction_type="work_related_training",
                amount=amount,
                max_annual_limit=None,
                confidence=0.70,
                description="Avdrag för arbetsrelaterad utbildning",
                requirements=[
                    "Direkt kopplat till nuvarande arbete",
                    "Bibehåller eller förbättrar yrkeskunskaper",
                    "Ej allmän utbildning",
                    "Ersätts ej av arbetsgivare"
                ],
                supporting_documents=["course_receipt", "work_relevance_proof", "employer_statement"],
                tax_savings_estimate=amount * 0.32
            ))
        
        return opportunities
    
    async def _analyze_charitable_donations(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for charitable donation deductions"""
        opportunities = []
        
        charity_rules = self.rules.get("Charitable Donations", {}).get("charitable_donations", {})
        min_donation = charity_rules.get("min_donation", 200)
        max_deduction = charity_rules.get("max_deduction", 6000)
        
        charity_keywords = [
            'röda korset', 'rädda barnen', 'unicef', 'amnesty', 'wwf', 'frälsningsarmén',
            'välgörenhet', 'donation', 'charity', 'humanitarian'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in charity_keywords):
            if amount >= min_donation:
                current_year_donations = user_profile.get('charity_donations_ytd', 0)
                remaining_limit = max_deduction - current_year_donations
                deductible_amount = min(amount, remaining_limit)
                
                if deductible_amount > 0:
                    opportunities.append(AvdragOpportunity(
                        category="Charitable Donations",
                        deduction_type="registered_charity",
                        amount=deductible_amount,
                        max_annual_limit=max_deduction,
                        confidence=0.85,
                        description=f"Gåvoavdrag för donation till registrerad organisation",
                        requirements=[
                            "Registrerad välgörenhetsorganisation",
                            f"Donation ≥{min_donation} SEK per organisation",
                            f"Max {max_deduction} SEK total per år"
                        ],
                        supporting_documents=["donation_receipt", "organization_registration"],
                        tax_savings_estimate=deductible_amount * 0.32
                    ))
        
        return opportunities
    
    async def _analyze_union_fees(self, vendor: str, amount: float, description: str, user_profile: dict) -> List[AvdragOpportunity]:
        """Analyze for union fees and professional membership deductions"""
        opportunities = []
        
        union_keywords = [
            'fackförbund', 'union', 'if metall', 'kommunal', 'unionen', 'saco', 'tco', 'lo',
            'a-kassa', 'arbetslöshetskassa', 'professional', 'membership', 'association'
        ]
        
        if any(keyword in vendor or keyword in description for keyword in union_keywords):
            opportunities.append(AvdragOpportunity(
                category="Union Fees",
                deduction_type="full_cost",
                amount=amount,
                max_annual_limit=None,
                confidence=0.90,
                description="Avdrag för fackföreningsavgift eller yrkesmedlemskap",
                requirements=[
                    "Arbetsrelaterat medlemskap",
                    "Ej socialt eller rekreativt syfte"
                ],
                supporting_documents=["membership_receipt", "union_confirmation"],
                tax_savings_estimate=amount * 0.32
            ))
        
        return opportunities
    
    async def optimize_family_taxes(self, family_data: dict) -> List[Dict[str, Any]]:
        """
        Optimize taxes for family situations (married/sambo/children)
        
        Args:
            family_data: Information about family members, incomes, expenses
            
        Returns:
            List of family tax optimization strategies
        """
        strategies = []
        
        family_status = family_data.get('status', 'single')  # single, married, sambo
        children = family_data.get('children', [])
        spouse_income = family_data.get('spouse_income', 0)
        user_income = family_data.get('user_income', 0)
        
        if family_status in ['married', 'sambo']:
            # Income splitting opportunities
            if abs(user_income - spouse_income) > 50000:
                strategies.append({
                    'strategy': 'income_optimization',
                    'description': 'Optimera inkomstfördelning mellan partners',
                    'potential_savings': self._calculate_tax_bracket_savings(user_income, spouse_income),
                    'actions': [
                        'Överväg att höginkomsttagare bidrar mer till pensionssparande',
                        'Låginkomsttagare kan ta mer utdelningar från investeringar',
                        'Koordinera ROT/RUT-avdrag mellan partners'
                    ]
                })
        
        if children:
            # Child-related benefits and optimizations
            strategies.append({
                'strategy': 'child_benefits_optimization',
                'description': 'Maximera barnrelaterade förmåner',
                'benefits': {
                    'barnbidrag_monthly': 1330 * len(children),
                    'large_family_supplement': self._calculate_large_family_supplement(len(children)),
                    'childcare_deductions': 'Kontrollera vårdnadsbidrag och förskole-/fritidskostnader'
                }
            })
        
        return strategies
    
    def _calculate_tax_bracket_savings(self, income1: float, income2: float) -> float:
        """Calculate potential tax savings from income optimization"""
        # Simplified tax bracket calculation
        municipal_rate = 0.32  # Average Swedish municipal tax
        state_tax_threshold = 598500  # 2024 threshold
        
        total_income = income1 + income2
        optimized_income = total_income / 2
        
        current_tax = self._calculate_tax(income1) + self._calculate_tax(income2)
        optimized_tax = 2 * self._calculate_tax(optimized_income)
        
        return max(0, current_tax - optimized_tax)
    
    def _calculate_tax(self, income: float) -> float:
        """Simplified Swedish tax calculation"""
        municipal_rate = 0.32
        state_tax_threshold = 598500
        state_tax_rate = 0.20
        
        municipal_tax = income * municipal_rate
        state_tax = max(0, (income - state_tax_threshold) * state_tax_rate)
        
        return municipal_tax + state_tax
    
    def _calculate_large_family_supplement(self, num_children: int) -> float:
        """Calculate large family supplement based on number of children"""
        if num_children < 2:
            return 0
        
        supplements = {2: 138, 3: 693, 4: 1693}
        if num_children >= 5:
            return 2193
        
        return supplements.get(num_children, 0)


async def discover_all_avdrag(receipt_data: dict, user_profile: dict) -> Dict[str, Any]:
    """
    Main entry point for discovering all tax deductions from a receipt/transaction
    
    Args:
        receipt_data: Extracted receipt information
        user_profile: User financial and personal information
        
    Returns:
        Complete analysis with all discovered opportunities
    """
    engine = SwedishTaxRuleEngine()
    opportunities = await engine.analyze_receipt(receipt_data, user_profile)
    
    # Calculate total potential savings
    total_savings = sum(opp.tax_savings_estimate for opp in opportunities)
    
    # Group by category
    by_category = {}
    for opp in opportunities:
        if opp.category not in by_category:
            by_category[opp.category] = []
        by_category[opp.category].append({
            'type': opp.deduction_type,
            'amount': opp.amount,
            'confidence': opp.confidence,
            'description': opp.description,
            'requirements': opp.requirements,
            'tax_savings': opp.tax_savings_estimate
        })
    
    return {
        'total_opportunities': len(opportunities),
        'total_potential_savings': total_savings,
        'opportunities_by_category': by_category,
        'recommendations': [
            f"Spara kvittot för {opp.category} - potentiell skattebesparing: {opp.tax_savings_estimate:.0f} SEK"
            for opp in opportunities if opp.confidence > 0.7
        ]
    }