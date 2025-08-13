"""
Swedish Tax & Accounting Knowledge Base
Built from Skatteverket, BFN, and Bolagsverket documentation
"""

from typing import Dict, List, Any
import json
from pathlib import Path

class SwedishTaxKnowledgeBase:
    """
    Knowledge base containing Swedish tax rules, regulations, and optimization strategies.
    This should be populated from official sources:
    - Skatteverket.se documentation
    - BFN standards
    - Bokföringslagen
    - Bolagsverket requirements
    """
    
    def __init__(self):
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load pre-processed Swedish tax documentation.

        Supports local JSON snippets in ./kb/*.json and falls back to built-in
        minimal rules if none found.
        """
        
        # Try load local snippets first
        try:
            kb_dir = Path("kb")
            if kb_dir.exists():
                for p in kb_dir.glob("*.json"):
                    try:
                        obj = json.loads(p.read_text(encoding="utf-8"))
                        section = obj.get("section") or p.stem
                        # Merge into tax_rules under custom section
                        self.tax_rules = getattr(self, "tax_rules", {})
                        self.tax_rules[section] = obj
                    except Exception:
                        continue
        except Exception:
            pass

        # CRITICAL: These need to be populated from actual Skatteverket docs
        self.tax_rules = {
            "representation": {
                "source": "Skatteverket - Representation och gåvor",
                "url": "https://www.skatteverket.se/foretag/skatterochavdrag/utgifteriforetaget/representationochgavor",
                "rules": {
                    "internal_representation": {
                        "deductible": 1.0,  # 100% deductible
                        "max_per_person_year": 0,  # No limit
                        "description": "Intern representation (personalfest, konferens)"
                    },
                    "external_representation": {
                        "deductible": 0.5,  # 50% deductible  
                        "max_per_person_year": 0,  # No limit but must be reasonable
                        "description": "Extern representation (kundmöten, affärsluncher)"
                    },
                    "gifts_employees": {
                        "deductible": 1.0,
                        "max_per_person_year": 450,  # SEK, excl VAT
                        "description": "Gåvor till anställda (jubileum, jul)"
                    },
                    "gifts_business": {
                        "deductible": 0.0,  # Not deductible
                        "max_per_gift": 180,  # SEK, excl VAT
                        "description": "Reklamgåvor till kunder"
                    }
                }
            },
            
            "travel_expenses": {
                "source": "Skatteverket - Resor i tjänsten",
                "url": "https://www.skatteverket.se/foretag/arbetsgivare/resorochbostader",
                "rules": {
                    "car_mileage": {
                        "rate_per_km": 1.85,  # SEK for 2024
                        "documentation": "Körjournal krävs"
                    },
                    "per_diem_domestic": {
                        "full_day": 240,  # SEK
                        "half_day": 120,  # SEK
                        "night_allowance": 120  # SEK
                    },
                    "per_diem_international": {
                        "varies_by_country": True,
                        "reference": "Skatteverket normalbelopp utland"
                    },
                    "accommodation": {
                        "deductible": 1.0,
                        "requirement": "Kvitto krävs, faktisk kostnad"
                    }
                }
            },
            
            "vat_rates": {
                "source": "Skatteverket - Momssatser",
                "url": "https://www.skatteverket.se/foretag/moms/saljavarorochtjanster/momssatser",
                "rates": {
                    "standard": {
                        "rate": 0.25,
                        "applies_to": "Allmän momssats för varor och tjänster"
                    },
                    "food_service": {
                        "rate": 0.12,
                        "applies_to": "Restaurang, catering, livsmedel"
                    },
                    "reduced": {
                        "rate": 0.06,
                        "applies_to": [
                            "Personbefordran (taxi, buss, tåg, flyg inom Sverige)",
                            "Böcker, tidningar, tidskrifter",
                            "Entré till konserter, bio, teater, idrottsevenemang",
                            "Hotell och camping"
                        ]
                    },
                    "exempt": {
                        "rate": 0.0,
                        "applies_to": [
                            "Sjukvård och tandvård",
                            "Social omsorg",
                            "Utbildning",
                            "Bank- och finanstjänster",
                            "Försäkringar"
                        ]
                    }
                }
            },
            
            "rd_deductions": {
                "source": "Skatteverket - FoU-avdrag",
                "url": "https://www.skatteverket.se/foretag/skatterochavdrag/forskningochutveckling",
                "rules": {
                    "qualifying_activities": [
                        "Grundforskning",
                        "Tillämpad forskning",
                        "Experimentell utveckling",
                        "Systematiskt arbete för ny kunskap"
                    ],
                    "deduction_rate": 1.0,  # 100% of costs
                    "additional_deduction": 0.2,  # Extra 20% for qualifying R&D
                    "requirements": [
                        "Dokumentation av FoU-projekt",
                        "Tidsredovisning för personal",
                        "Projektplan och målsättning"
                    ]
                }
            },
            
            "accounting_requirements": {
                "source": "Bokföringslagen (1999:1078)",
                "rules": {
                    "documentation": {
                        "required_info": [
                            "Verifikationsnummer",
                            "Transaktionsdatum",
                            "Vad transaktionen avser",
                            "Belopp",
                            "Motpart"
                        ],
                        "retention_period": 7,  # years
                        "format": "Läsbart format, WORM-lagring"
                    },
                    "timeliness": {
                        "cash_transactions": "Nästa arbetsdag",
                        "other_transactions": "Löpande, utan oskäligt dröjsmål",
                        "annual_report": "6 månader efter räkenskapsårets slut"
                    },
                    "good_accounting_practice": {
                        "reference": "BFN allmänna råd",
                        "principle": "God redovisningssed ska följas"
                    }
                }
            },
            
            "year_end_optimization": {
                "source": "Skatteverket - Bokslut och deklaration",
                "strategies": {
                    "accelerate_expenses": {
                        "when": "Vinst förväntas",
                        "actions": [
                            "Förskottsbetala hyra (max 1 år)",
                            "Köp inventarier före årsskifte",
                            "Betala leverantörsfakturor",
                            "Genomför planerat underhåll"
                        ]
                    },
                    "defer_income": {
                        "when": "Legal och inom god redovisningssed",
                        "actions": [
                            "Fakturera efter årsskifte",
                            "Periodisera intäkter korrekt"
                        ]
                    },
                    "provisions": {
                        "allowed": [
                            "Garantiavsättningar",
                            "Omstruktureringsreserver (specifika krav)",
                            "Pensionsavsättningar"
                        ]
                    },
                    "depreciation": {
                        "rules": "Räkenskapsenlig avskrivning eller restvärdesavskrivning",
                        "immediate_writeoff": "Inventarier under 0.5 prisbasbelopp"
                    }
                }
            },
            
            "reverse_charge_vat": {
                "source": "Skatteverket - Omvänd skattskyldighet",
                "url": "https://www.skatteverket.se/omvandskattskyldighet",
                "applies_to": {
                    "construction_services": {
                        "description": "Byggtjänster mellan näringsidkare",
                        "account_debit": "2645",  # Ingående moms
                        "account_credit": "2615"  # Utgående moms
                    },
                    "eu_services": {
                        "description": "Tjänster från EU-företag",
                        "requirement": "Giltigt EU-momsregistreringsnummer"
                    },
                    "scrap_metal": {
                        "description": "Handel med skrot och avfall"
                    }
                }
            }
        }
        
        # Vendor category mappings based on Swedish business patterns
        self.vendor_categories = {
            "restaurants": {
                "keywords": ["restaurang", "café", "krog", "bar", "lunch", "middag", 
                           "fika", "konditori", "pizzeria", "sushi", "grill"],
                "default_account": "5811",  # Representation
                "vat_rate": 0.12,
                "tax_treatment": "representation_external"
            },
            "transport": {
                "keywords": ["taxi", "uber", "bolt", "sj", "sas", "norwegian", 
                           "flygbussarna", "arlanda express", "pendeltåg", "tunnelbana"],
                "default_account": "5611",  # Resekostnader
                "vat_rate": 0.06,
                "tax_treatment": "travel_expenses"
            },
            "fuel": {
                "keywords": ["shell", "circle k", "preem", "okq8", "st1", "ingo",
                           "bensin", "diesel", "laddning"],
                "default_account": "5611",  # Bilkostnader
                "vat_rate": 0.25,
                "tax_treatment": "vehicle_expenses"
            },
            "office_supplies": {
                "keywords": ["kontorsmaterial", "clas ohlson", "kjell", "inet",
                           "dustin", "atea", "teknikmagasinet"],
                "default_account": "5410",  # Förbrukningsmaterial
                "vat_rate": 0.25,
                "tax_treatment": "standard_deduction"
            },
            "software": {
                "keywords": ["microsoft", "adobe", "slack", "zoom", "dropbox",
                           "google", "aws", "azure", "github", "saas", "licens"],
                "default_account": "5420",  # Programvaror
                "vat_rate": 0.25,
                "tax_treatment": "standard_deduction"
            },
            "consulting": {
                "keywords": ["konsult", "deloitte", "pwc", "ey", "kpmg", 
                           "grant thornton", "advokat", "jurist", "revisor"],
                "default_account": "6530",  # Redovisning och revision
                "vat_rate": 0.25,
                "tax_treatment": "professional_services"
            }
        }
        
        # Common Swedish accounting errors to prevent
        self.common_errors = {
            "mixed_private_business": {
                "description": "Privata utgifter bokförda som företagskostnader",
                "prevention": "Kräv affärssyfte dokumentation",
                "penalty_risk": "Skattetillägg 40% + ränta"
            },
            "missing_documentation": {
                "description": "Saknad verifikation/underlag",
                "prevention": "Blockera bokföring utan kvitto",
                "penalty_risk": "Bokföringsbrott, böter eller fängelse"
            },
            "incorrect_vat": {
                "description": "Fel momssats eller momskod",
                "prevention": "Automatisk momsberäkning baserat på kategori",
                "penalty_risk": "Skattetillägg + ränta på momsdifferens"
            },
            "late_reporting": {
                "description": "Sen momsdeklaration eller bokföring",
                "prevention": "Automatiska påminnelser och deadlines",
                "penalty_risk": "Förseningsavgift 1,250 SEK + skattetillägg"
            }
        }
    
    def get_tax_treatment(self, vendor: str, amount: float, description: str = "") -> Dict[str, Any]:
        """Get recommended tax treatment based on Swedish rules."""
        
        vendor_lower = vendor.lower()
        
        # Check vendor categories
        for category, config in self.vendor_categories.items():
            if any(keyword in vendor_lower for keyword in config["keywords"]):
                treatment = self.tax_rules.get(config["tax_treatment"], {})
                
                return {
                    "category": category,
                    "account": config["default_account"],
                    "vat_rate": config["vat_rate"],
                    "tax_treatment": config["tax_treatment"],
                    "deductible": treatment.get("deductible", 1.0),
                    "special_rules": treatment.get("rules", {}),
                    "documentation_required": self._get_required_docs(category, amount)
                }
        
        # Default treatment
        return {
            "category": "general",
            "account": "4000",  # Inköp av varor
            "vat_rate": 0.25,
            "tax_treatment": "standard_deduction",
            "deductible": 1.0,
            "special_rules": {},
            "documentation_required": ["Kvitto", "Affärssyfte"]
        }
    
    def _get_required_docs(self, category: str, amount: float) -> List[str]:
        """Get required documentation based on Swedish law."""
        
        docs = ["Kvitto/faktura med organisationsnummer"]
        
        if category == "restaurants" and amount > 1000:
            docs.extend([
                "Deltagarförteckning",
                "Syfte med representation",
                "Affärsrelation"
            ])
        
        if category == "transport" and amount > 500:
            docs.append("Resans syfte och destination")
        
        if category == "consulting" and amount > 10000:
            docs.extend([
                "Avtal eller offert",
                "Specifikation av utfört arbete"
            ])
        
        return docs
    
    def validate_compliance(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction against Swedish law."""
        
        issues = []
        warnings = []
        score = 100
        
        # Check required fields (Bokföringslagen)
        required_fields = ["date", "amount", "counterparty", "description"]
        for field in required_fields:
            if not transaction.get(field):
                issues.append(f"Saknar {field} (Bokföringslagen krav)")
                score -= 20
        
        # Check cash transaction timeliness
        if transaction.get("payment_method") == "cash":
            if transaction.get("days_old", 0) > 1:
                issues.append("Kontanttransaktion ej bokförd nästa arbetsdag")
                score -= 15
        
        # Check amount reasonableness
        amount = transaction.get("amount", 0)
        if amount > 100000:
            warnings.append("Stort belopp - säkerställ dokumentation")
            score -= 5
        
        # Check VAT consistency
        vat_amount = transaction.get("vat_amount", 0)
        if vat_amount > 0:
            implied_rate = vat_amount / (amount - vat_amount)
            valid_rates = [0.25, 0.12, 0.06]
            if not any(abs(implied_rate - rate) < 0.01 for rate in valid_rates):
                warnings.append(f"Ovanlig momssats: {implied_rate:.1%}")
                score -= 10
        
        return {
            "compliant": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
            "warnings": warnings,
            "regulations_checked": [
                "Bokföringslagen (1999:1078)",
                "Mervärdesskattelagen (1994:200)",
                "BFN allmänna råd"
            ]
        }


class SwedishTaxRAG:
    """Minimal RAG facade to retrieve grounded snippets.

    This is a stub that returns knowledge base slices; replace with a real vector store when available.
    """

    def __init__(self, kb: SwedishTaxKnowledgeBase):
        self.kb = kb

    def search(self, query: str, k: int = 3) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        # Very light keyword routing to examples
        if "representation" in query.lower():
            results.append({
                "title": "Representation (Skatteverket)",
                "snippet": "Extern representation 50% avdragsgill, intern representation 100%.",
                "url": self.kb.tax_rules["representation"]["url"],
            })
        if "moms" in query.lower() or "vat" in query.lower():
            results.append({
                "title": "Momssatser (Skatteverket)",
                "snippet": "25% standard, 12% restaurang, 6% personbefordran och kultur.",
                "url": self.kb.tax_rules["vat_rates"]["url"],
            })
        return results[:k]


# Singleton instance
_knowledge_base: SwedishTaxKnowledgeBase = None

def get_knowledge_base() -> SwedishTaxKnowledgeBase:
    """Get or create knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = SwedishTaxKnowledgeBase()
    return _knowledge_base