from locust import HttpUser, task, between
import random

class GatewayUser(HttpUser):
    # Simula um usuário pensando entre 1 a 3 segundos antes de mandar outra mensagem
    wait_time = between(15, 20)

    @task
    def testar_gateway(self):
        # 1. Escolhemos o "crachá" do usuário aleatoriamente
        api_keys = ["premium-key-123", "free-key-456"]
        chave_escolhida = random.choice(api_keys)
        
        # 2. Montamos o cabeçalho de segurança exigido pela sua Aduana
        headers = {
            "Authorization": f"Bearer {chave_escolhida}"
        }

        # 3. Geramos o ID para evitar o Cache Hit imediato (se o objetivo for testar os provedores)
        random_id = random.randint(1, 10000)
        
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": f"Qual o sentido da vida? {random_id}"}]
        }

        # 4. Disparamos o ataque enviando os headers junto com o payload
        
        with self.client.post("/v1/chat/completions", json=payload, headers=headers, catch_response=True, stream=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha: Status {response.status_code} | Resposta: {response.text}")