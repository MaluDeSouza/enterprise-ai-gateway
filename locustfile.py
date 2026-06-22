from locust import HttpUser, task, between
import random

class GatewayUser(HttpUser):
    # Simula um usuário pensando entre 1 a 3 segundos antes de mandar outra mensagem
    wait_time = between(1, 3)

    @task
    def testar_gateway(self):
        # Geramos uma pergunta aleatória para evitar o Cache Hit e forçar a requisição a bater na IA.
        # Queremos testar a resiliência da "OpenAI" e o Fallback!
        random_id = random.randint(1, 10000)
        
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": f"Qual o sentido da vida? {random_id}"}],
            "tenant_tier": "premium" # Usamos premium para tentar forçar a OpenAI
        }

        # Dispara o ataque contra o nosso cano principal
        with self.client.post("/v1/chat/completions", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"O Gateway falhou e devolveu status {response.status_code}")