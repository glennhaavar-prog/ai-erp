"""
AI Client Service - Wrapper for Claude/GPT API calls with error handling and retry logic.

This service implements:
- Retry logic with exponential backoff (ERROR_HANDLING_SPEC.md)
- Graceful degradation when AI fails
- Standardized error responses
- Confidence scoring fallback
- Logging and monitoring

Usage:
    from app.services.ai_client import AIClient
    
    ai = AIClient()
    
    # With automatic retry
    response = await ai.chat_completion(
        messages=[{"role": "user", "content": "Analyze this invoice"}],
        system="You are an accounting assistant"
    )
    
    # Graceful degradation - returns None on failure
    response = await ai.chat_completion_safe(
        messages=[...],
        fallback_value=None
    )
"""
import logging
from typing import Dict, Any, List, Optional, Union
from anthropic import Anthropic, AsyncAnthropic, APIError, APITimeoutError, RateLimitError
from app.config import settings
from app.utils.errors import AIServiceError, AITimeoutError
from app.utils.retry import retry_with_backoff, AI_RETRY_CONFIG

logger = logging.getLogger(__name__)


class AIClient:
    """
    Wrapped AI client with error handling and retry logic.
    
    Supports Claude (default) and GPT (future).
    """
    
    def __init__(self, provider: str = "claude"):
        """
        Initialize AI client.
        
        Args:
            provider: "claude" or "gpt" (gpt not yet implemented)
        """
        self.provider = provider
        
        if provider == "claude":
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not configured - AI features will fail")
                raise ValueError("ANTHROPIC_API_KEY not configured")
            
            self.client = Anthropic(api_key=api_key)
            self.async_client = AsyncAnthropic(api_key=api_key)
            self.default_model = "claude-sonnet-4-5"
        
        elif provider == "gpt":
            raise NotImplementedError("GPT provider not yet implemented")
        
        else:
            raise ValueError(f"Unknown AI provider: {provider}")
    
    @retry_with_backoff(AI_RETRY_CONFIG)
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion with retry logic.
        
        Raises:
            AIServiceError: On API failure after all retries
            AITimeoutError: On timeout after all retries
        
        Returns:
            str: Response text from AI
        """
        if not model:
            model = self.default_model
        
        try:
            if self.provider == "claude":
                response = await self.async_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system or "You are a helpful assistant.",
                    messages=messages
                )
                
                # Extract text from Claude response
                return response.content[0].text
            
            else:
                raise NotImplementedError(f"Provider {self.provider} not implemented")
        
        except APITimeoutError as e:
            logger.error(f"AI API timeout: {e}")
            raise AITimeoutError(timeout_seconds=30, details={"error": str(e)})
        
        except RateLimitError as e:
            logger.error(f"AI API rate limit: {e}")
            raise AIServiceError(
                message="API rate limit nådd - prøv igjen om litt",
                details={"error": str(e), "type": "rate_limit"}
            )
        
        except APIError as e:
            logger.error(f"AI API error: {e}")
            raise AIServiceError(
                message=f"AI-tjenesten svarte ikke: {e}",
                details={"error": str(e), "type": "api_error"}
            )
        
        except Exception as e:
            logger.error(f"Unexpected AI error: {e}")
            raise AIServiceError(
                message="Ukjent feil med AI-tjenesten",
                details={"error": str(e), "type": "unknown"}
            )
    
    async def chat_completion_safe(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        fallback_value: Any = None
    ) -> Union[str, Any]:
        """
        Chat completion with graceful degradation.
        
        Returns fallback_value on any error (doesn't raise exceptions).
        
        Use this when AI failure shouldn't block the user workflow.
        
        Example:
            # Get AI suggestion, but allow manual booking if AI fails
            suggestion = await ai.chat_completion_safe(
                messages=[...],
                fallback_value=None
            )
            
            if suggestion is None:
                # AI failed - fall back to manual mode
                confidence = 0
                manual_mode = True
            else:
                confidence = 85
        """
        try:
            return await self.chat_completion(
                messages=messages,
                system=system,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
        
        except (AIServiceError, AITimeoutError) as e:
            logger.warning(f"AI call failed (graceful degradation): {e}")
            return fallback_value
        
        except Exception as e:
            logger.error(f"Unexpected error in safe AI call: {e}")
            return fallback_value
    
    async def analyze_invoice(
        self,
        invoice_data: Dict[str, Any],
        chart_of_accounts: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze vendor invoice and suggest booking.
        
        Returns None if AI fails (graceful degradation).
        
        Returns:
            Dict with suggested_account, vat_code, confidence, reasoning
            or None on failure
        """
        # Build prompt
        system_prompt = """Du er en norsk autorisert regnskapsfører.
Analyser fakturaen og foreslå riktig konto for bokføring.

Returner JSON med:
{
  "suggested_account": "6700",
  "vat_code": "5",
  "confidence": 85,
  "reasoning": "Forklaring på hvorfor denne kontoen ble valgt"
}"""
        
        # Format invoice data
        invoice_text = f"""
Leverandør: {invoice_data.get('vendor_name', 'Unknown')}
Fakturanummer: {invoice_data.get('invoice_number', 'N/A')}
Beløp: {invoice_data.get('amount', 0)} {invoice_data.get('currency', 'NOK')}
Beskrivelse: {invoice_data.get('description', 'Ingen beskrivelse')}

Tilgjengelige kontoer:
{self._format_chart_of_accounts(chart_of_accounts[:20])}  # Top 20 most common
"""
        
        response = await self.chat_completion_safe(
            messages=[{"role": "user", "content": invoice_text}],
            system=system_prompt,
            fallback_value=None
        )
        
        if response is None:
            return None
        
        # Parse JSON response
        try:
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            return result
        
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}\nResponse: {response}")
            return None
    
    def _format_chart_of_accounts(self, accounts: List[Dict[str, str]]) -> str:
        """Format chart of accounts for AI prompt."""
        lines = []
        for acc in accounts:
            lines.append(f"- {acc.get('number', '')}: {acc.get('name', '')}")
        return "\n".join(lines)
    
    async def explain_account(
        self,
        account_number: str,
        account_name: str
    ) -> str:
        """
        Explain what an account code is used for.
        
        Returns empty string on failure (graceful degradation).
        """
        system_prompt = "Du er en norsk autorisert regnskapsfører. Forklar kort hva denne kontoen brukes til."
        
        response = await self.chat_completion_safe(
            messages=[{"role": "user", "content": f"Konto {account_number} - {account_name}"}],
            system=system_prompt,
            max_tokens=256,
            fallback_value=""
        )
        
        return response
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if AI service is healthy.
        
        Returns:
            Dict with status and latency
        """
        import time
        start = time.time()
        
        try:
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "ping"}],
                system="Reply with 'pong'",
                max_tokens=10
            )
            
            latency = time.time() - start
            
            return {
                "status": "healthy",
                "provider": self.provider,
                "model": self.default_model,
                "latency_seconds": round(latency, 3),
                "response": response.strip()
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider,
                "error": str(e)
            }


# Singleton instance
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """
    Get singleton AI client instance.
    
    Usage:
        from app.services.ai_client import get_ai_client
        
        ai = get_ai_client()
        response = await ai.chat_completion(...)
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient(provider="claude")
    return _ai_client
