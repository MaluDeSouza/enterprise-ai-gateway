from src.providers.gemini import GeminiProvider
from src.providers.ollama import OllamaProvider
from src.auth.models import Tenant
from src.core.circuit_breaker import CircuitBreaker

class PolicyEngine:
    def __init__(self, circuit_breaker: CircuitBreaker):
        # Injetamos o disjuntor para que o motor tome decisões conscientes
        self.circuit_breaker = circuit_breaker

    def get_provider_for_tenant(self, tenant: Tenant) -> tuple:
        """
        Decide a IA baseada no plano do cliente interno e na saúde da API externa.
        Retorna a instância do provedor e uma string descritiva da origem.
        """
        if tenant.tier.lower() == "premium":
            # Premium tem direito ao Gemini, MAS verificamos se a API não está caída
            if self.circuit_breaker.can_route():
                return GeminiProvider(), "Gemini (API Real)"
            else:
                return OllamaProvider(), "Ollama (Fallback Mock - Circuito Aberto)"
        
        # Free ou qualquer outra coisa cai no local
        return OllamaProvider(), "Ollama (Free Tier Mock)"