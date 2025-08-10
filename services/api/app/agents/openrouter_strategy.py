"""
OpenRouter Integration Strategy for Bertil-AI
Leveraging 1000 free requests/day for Swedish accounting automation
"""

from enum import Enum
from typing import Dict, Any, Optional
import os

class OpenRouterModels(Enum):
    """Best free models for our use case (with :free suffix on OpenRouter)."""
    
    # Tier 1: Primary Models (Best for Swedish + Accounting)
    DEEPSEEK_CHAT = "deepseek/deepseek-chat:free"  # Best overall, strong coding/logic
    LLAMA_3_70B = "meta-llama/llama-3-70b-instruct:free"  # Excellent multilingual
    
    # Tier 2: Visual/OCR Models  
    QWEN_2_5_VL = "qwen/qwen-2.5-vl-32b:free"  # Best for OCR/visual tasks
    GEMINI_FLASH = "google/gemini-flash-1.5:free"  # Good for document understanding
    
    # Tier 3: Fallback Models
    MIXTRAL_8X7B = "mistralai/mixtral-8x7b-instruct:free"  # Good general purpose
    GEMMA_27B = "google/gemma-2-27b:free"  # Decent but limited Swedish
    
    # Tier 4: Fast/Simple Tasks
    PHI_3 = "microsoft/phi-3-mini:free"  # Very fast, basic tasks
    GEMMA_7B = "google/gemma-7b:free"  # Quick validation


class TaskComplexity(Enum):
    """Task complexity levels for model selection."""
    SIMPLE = "simple"  # Basic extraction, validation
    MEDIUM = "medium"  # Swedish text, basic accounting
    COMPLEX = "complex"  # Tax optimization, compliance
    VISUAL = "visual"  # OCR, receipt processing


class OpenRouterStrategy:
    """
    Optimal strategy for 1000 free requests/day.
    
    Key insights:
    1. DeepSeek Chat is surprisingly good for accounting/math
    2. Llama 3 70B handles Swedish excellently
    3. Qwen 2.5 VL is best for OCR/visual tasks
    4. Use tiered approach to maximize free tier
    """
    
    def __init__(self):
        # Must have $10+ credit for 1000 requests/day
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.daily_limit = 1000
        self.requests_today = 0
        
    def select_model(self, task_type: str, complexity: TaskComplexity) -> str:
        """
        Smart model selection based on task requirements.
        
        Strategy:
        - Use best models for complex tasks
        - Use fast models for simple validation
        - Reserve visual models for OCR only
        """
        
        # Visual tasks (OCR, receipt processing)
        if complexity == TaskComplexity.VISUAL:
            if self.requests_today < 200:  # Use best model early in day
                return OpenRouterModels.QWEN_2_5_VL.value
            else:
                return OpenRouterModels.GEMINI_FLASH.value
        
        # Complex tasks (tax optimization, compliance)
        if complexity == TaskComplexity.COMPLEX:
            # DeepSeek for accounting/math, Llama for Swedish
            if "tax" in task_type or "accounting" in task_type:
                return OpenRouterModels.DEEPSEEK_CHAT.value
            else:
                return OpenRouterModels.LLAMA_3_70B.value
        
        # Medium tasks (standard bookkeeping)
        if complexity == TaskComplexity.MEDIUM:
            if self.requests_today < 500:
                return OpenRouterModels.MIXTRAL_8X7B.value
            else:
                return OpenRouterModels.GEMMA_27B.value
        
        # Simple tasks (validation, extraction)
        return OpenRouterModels.PHI_3.value
    
    def estimate_daily_usage(self, users: int = 100) -> Dict[str, Any]:
        """
        Estimate daily usage for gradual rollout.
        
        With 1000 free requests/day:
        - 100 users × 10 receipts/day = 1000 requests (perfect fit!)
        - Can handle initial pilot perfectly
        """
        
        receipts_per_user = 10
        total_requests = users * receipts_per_user
        
        return {
            "users_supported": min(users, 100),  # Max 100 users on free tier
            "receipts_per_day": min(total_requests, 1000),
            "coverage": min(100, (1000 / total_requests) * 100),
            "cost": "$0" if total_requests <= 1000 else f"${(total_requests - 1000) * 0.001:.2f}",
            "recommendation": self._get_recommendation(total_requests)
        }
    
    def _get_recommendation(self, total_requests: int) -> str:
        """Recommendation based on usage."""
        
        if total_requests <= 500:
            return "Perfect for development and testing"
        elif total_requests <= 1000:
            return "Ideal for pilot with 100 users"
        elif total_requests <= 5000:
            return "Add paid credits for overflow ($5-10/day)"
        else:
            return "Consider dedicated deployment or OpenAI API"


class SwedishAccountingPrompts:
    """Optimized prompts for Swedish accounting with free models."""
    
    @staticmethod
    def receipt_extraction(ocr_text: str, model: str) -> str:
        """Prompt optimized for free models."""
        
        # Shorter, more direct prompts for free models
        if "phi" in model or "gemma-7b" in model:
            return f"""
            Extract from receipt:
            {ocr_text[:500]}
            
            Return JSON only:
            vendor, amount, date, vat_rate (0.25/0.12/0.06)
            """
        
        # More detailed for capable models
        return f"""
        Swedish receipt analysis. Extract:
        
        Text: {ocr_text[:1000]}
        
        Requirements:
        1. Vendor name (företag)
        2. Total amount (SEK)
        3. VAT/moms (25%=general, 12%=mat, 6%=transport)
        4. Date (YYYY-MM-DD)
        5. Category (restaurang/transport/kontor/etc)
        
        Swedish VAT rules:
        - Restaurang/mat: 12% moms
        - Taxi/transport: 6% moms  
        - Standard: 25% moms
        
        Return structured JSON.
        """
    
    @staticmethod
    def tax_optimization(transaction: Dict[str, Any]) -> str:
        """Swedish tax optimization prompt."""
        
        return f"""
        Optimize Swedish business expense for tax:
        
        Transaction: {transaction}
        
        Check against Swedish tax rules:
        1. Representation: 50% avdragsgill (Bokföringslagen)
        2. Resor: Full avdrag, 6% moms (taxi)
        3. FoU: Extra 20% avdrag möjligt
        4. Kontor: Full avdrag
        
        Return:
        - Recommended account (5xxx/6xxx)
        - Tax savings (SEK)
        - Explanation (Swedish law reference)
        """


class ProductionImplementation:
    """How to implement with OpenRouter free tier."""
    
    def __init__(self):
        self.strategy = OpenRouterStrategy()
        
    async def process_receipt_smartly(self, image_path: str) -> Dict[str, Any]:
        """
        Smart processing using free tier optimally.
        
        Approach:
        1. Use fast model for initial validation
        2. Use visual model for OCR if needed
        3. Use capable model for complex extraction
        4. Cache aggressively
        """
        
        # Step 1: Quick validation with Phi-3 (fast, cheap)
        is_receipt = await self._quick_validate(image_path)
        if not is_receipt:
            return {"error": "Not a valid receipt"}
        
        # Step 2: OCR with Qwen (best visual model)
        ocr_result = await self._extract_with_ocr(image_path)
        
        # Step 3: Swedish processing with Llama 3 70B
        extracted = await self._process_swedish(ocr_result)
        
        # Step 4: Tax optimization with DeepSeek
        optimized = await self._optimize_tax(extracted)
        
        return {
            "extracted": extracted,
            "optimized": optimized,
            "requests_used": 4,
            "daily_remaining": 1000 - self.strategy.requests_today
        }
    
    async def _quick_validate(self, image_path: str) -> bool:
        """Use fast model for validation."""
        model = self.strategy.select_model("validate", TaskComplexity.SIMPLE)
        # Implementation here
        return True
    
    async def _extract_with_ocr(self, image_path: str) -> str:
        """Use visual model for OCR."""
        model = self.strategy.select_model("ocr", TaskComplexity.VISUAL)
        # Implementation here
        return "OCR text"
    
    async def _process_swedish(self, text: str) -> Dict[str, Any]:
        """Use Swedish-capable model."""
        model = self.strategy.select_model("swedish", TaskComplexity.MEDIUM)
        # Implementation here
        return {}
    
    async def _optimize_tax(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Use math-capable model for tax."""
        model = self.strategy.select_model("tax", TaskComplexity.COMPLEX)
        # Implementation here
        return {}


# Usage recommendations
"""
ROLLOUT STRATEGY WITH OPENROUTER FREE TIER:

Phase 1 (Week 1): Development & Testing
- Use all 1000 requests/day for testing
- Test all models to find best performers
- Cache everything for reuse

Phase 2 (Week 2): Pilot with 10 users
- 10 users × 10 receipts = 100 requests/day
- Plenty of headroom for testing
- Validate Swedish accuracy

Phase 3 (Week 3): Scale to 50 users  
- 50 users × 10 receipts = 500 requests/day
- Still within free tier
- Start optimizing model selection

Phase 4 (Week 4): Production with 100 users
- 100 users × 10 receipts = 1000 requests/day
- Perfect fit for free tier!
- Add $10-20/day for overflow

Phase 5 (Month 2+): Scale beyond
- Add OpenAI API for overflow
- Keep OpenRouter for development
- Consider local deployment of DeepSeek

COST PROJECTION:
- First 100 users: FREE (with $10 credit balance)
- 101-500 users: ~$20/day overflow
- 501-1000 users: ~$50/day
- 1000+ users: Switch to OpenAI/Anthropic

This is PERFECT for your gradual rollout!
"""