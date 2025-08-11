"""
LLM Integration Module - Connect to OpenAI/Anthropic/OpenRouter/Local Models
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    AZURE_OPENAI = "azure_openai"
    OPENROUTER = "openrouter"
    LOCAL = "local"  # Ollama/llama.cpp

@dataclass
class LLMConfig:
    provider: LLMProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.1  # Low for accuracy
    max_tokens: int = 2000

class LLMService:
    """Unified LLM service for all agents."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._init_client()
        
    def _init_client(self):
        """Initialize the appropriate LLM client."""
        if self.config.provider == LLMProvider.OPENAI:
            # Lazy import to avoid hard dependency when not used
            import openai  # type: ignore
            openai.api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            self.client = openai
            
        elif self.config.provider == LLMProvider.ANTHROPIC:
            # Lazy import
            import anthropic  # type: ignore
            self.client = anthropic.Anthropic(
                api_key=self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            )
            
        elif self.config.provider == LLMProvider.AZURE_OPENAI:
            import openai  # type: ignore
            openai.api_type = "azure"
            openai.api_base = self.config.base_url
            openai.api_key = self.config.api_key
            self.client = openai
        
        elif self.config.provider == LLMProvider.OPENROUTER:
            # Use dedicated OpenRouter client
            from .openrouter_integration import get_openrouter_client
            self.client = get_openrouter_client()
            
        elif self.config.provider == LLMProvider.LOCAL:
            # For Ollama or llama.cpp
            self.base_url = self.config.base_url or "http://localhost:11434"
            
    async def extract_receipt_data(self, ocr_text: str) -> Dict[str, Any]:
        """Enhanced receipt data extraction using LLM."""
        
        prompt = f"""
        Analyze this Swedish receipt/invoice and extract structured data.
        
        OCR Text:
        {ocr_text}
        
        Extract and return JSON:
        {{
            "vendor": "company name",
            "total_amount": numeric_value,
            "vat_amount": numeric_value,
            "vat_rate": 0.25/0.12/0.06,
            "date": "YYYY-MM-DD",
            "invoice_number": "if present",
            "category": "restaurant/travel/office/etc",
            "confidence": 0.0-1.0
        }}
        
        Swedish VAT rules:
        - Restaurants/food: 12% (moms)
        - Transport/taxi: 6% 
        - General goods: 25%
        - Books/media: 6%
        
        Be precise with Swedish formats (SEK, dates, org numbers).
        """
        
        if self.config.provider == LLMProvider.OPENAI:
            response = await self._openai_complete(prompt)
            return self._parse_json_response(response)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            response = await self._anthropic_complete(prompt)
            return self._parse_json_response(response)
        elif self.config.provider == LLMProvider.OPENROUTER:
            # Use Swedish model, force JSON
            resp = await self.client._call_openrouter(  # type: ignore[attr-defined]
                model=self.client.models.get("swedish", "meta-llama/llama-3.1-70b-instruct:free"),
                prompt=prompt,
                task_type="extraction",
                temperature=self.config.temperature,
            )
            return resp if isinstance(resp, dict) else {"raw_response": str(resp)}
        else:
            response = await self._local_complete(prompt)
            return self._parse_json_response(response)
    
    async def optimize_tax(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Swedish tax optimization using LLM with Skatteverket rules."""
        
        prompt = f"""
        Analyze this Swedish business transaction for tax optimization opportunities.
        
        Transaction:
        {verification_data}
        
        Apply Swedish tax rules:
        1. Representation (Bokföringslagen 4 kap 2§): 50% deductible
        2. Travel (Inkomstskattelagen 16 kap): Full deductible, 6% VAT
        3. R&D (FoU-avdrag): Enhanced deductions available
        4. Meal deductions: Max 120 SEK per meal
        5. Car expenses: 1.85 SEK/km deductible
        
        Return optimization suggestions with exact SEK savings.
        Consider timing (year-end), account classification, and VAT optimization.
        
        Format response as JSON with specific actions and savings.
        """
        
        response = await self._get_completion(prompt)
        return self._parse_json_response(response)
    
    async def check_compliance(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Swedish compliance checking using LLM."""
        
        prompt = f"""
        Check this transaction against Swedish accounting law (Bokföringslagen) and tax regulations.
        
        Transaction:
        {transaction}
        
        Validate against:
        1. Bokföringslagen requirements (complete documentation, timeliness)
        2. Skatteverket VAT rules (correct rates, reverse charge)
        3. BFN standards (accounting principles)
        4. Money laundering regulations (cash limits, suspicious patterns)
        5. GDPR compliance (personal data handling)
        
        Return:
        - compliance_score (0-100)
        - issues (critical problems)
        - warnings (potential problems)
        - recommendations (how to fix)
        
        Be strict - it's better to flag potential issues than miss real problems.
        """
        
        response = await self._get_completion(prompt)
        return self._parse_json_response(response)
    
    async def generate_insights(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contextual business insights using LLM."""
        
        prompt = f"""
        Analyze this Swedish business data and provide actionable insights.
        
        Business Data:
        {business_data}
        
        Generate insights for:
        1. Expense trends and anomalies
        2. Cash flow risks and opportunities
        3. Tax optimization windows
        4. Vendor relationship risks
        5. Seasonal patterns
        
        Each insight should include:
        - title (Swedish or English)
        - message (specific and actionable)
        - impact (SEK value if applicable)
        - urgency (immediate/daily/weekly/monthly)
        - action (what to do)
        
        Focus on Swedish business context and regulations.
        """
        
        response = await self._get_completion(prompt)
        return self._parse_json_response(response)
    
    async def _get_completion(self, prompt: str) -> str:
        """Route to appropriate provider."""
        if self.config.provider == LLMProvider.OPENAI:
            return await self._openai_complete(prompt)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_complete(prompt)
        elif self.config.provider == LLMProvider.OPENROUTER:
            # For generic completions via OpenRouter when not strict JSON
            resp = await self.client._call_openrouter(  # type: ignore[attr-defined]
                model=self.client.models.get("swedish", "meta-llama/llama-3.1-70b-instruct:free"),
                prompt=prompt,
                task_type="general",
                temperature=self.config.temperature,
            )
            # Return a string for downstream parsing compatibility
            return json.dumps(resp, ensure_ascii=False)
        else:
            return await self._local_complete(prompt)
    
    async def _openai_complete(self, prompt: str) -> str:
        """OpenAI completion."""
        import openai  # type: ignore
        response = await openai.ChatCompletion.acreate(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "You are a Swedish accounting and tax expert AI assistant. Always follow Swedish law and regulations."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.choices[0].message.content
    
    async def _anthropic_complete(self, prompt: str) -> str:
        """Anthropic Claude completion."""
        # anthropic is imported in _init_client
        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system="You are a Swedish accounting and tax expert AI assistant. Always follow Swedish law and regulations.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _local_complete(self, prompt: str) -> str:
        """Local model completion (Ollama/llama.cpp)."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "temperature": self.config.temperature
                }
            ) as response:
                result = await response.json()
                return result.get("response", "")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        import re
        
        # Extract JSON from response (LLMs often add explanation)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback to parsing key-value pairs
        return {"raw_response": response, "parse_error": True}


# Singleton instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        config = LLMConfig(
            provider=LLMProvider(os.getenv("LLM_PROVIDER", "openai")),
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4-turbo-preview"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1"))
        )
        _llm_service = LLMService(config)
    return _llm_service