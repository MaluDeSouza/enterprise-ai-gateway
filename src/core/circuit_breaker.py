import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "CLOSED"       # Tudo normal, requisições fluindo para o provider principal.
    OPEN = "OPEN"           # Falhas excederam o limite, acionar fallback.
    HALF_OPEN = "HALF_OPEN" # Tempo de castigo passou, testando se a IA voltou.

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def can_route(self) -> bool:
        """
        Define se a requisição pode passar para o provedor principal.
        Retorna False se o circuito estiver aberto (hora do fallback).
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Já passou o tempo de espera (60s)?
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        return self.state == CircuitState.HALF_OPEN

    def record_success(self):
        """A chamada deu certo. Reseta os contadores e fecha o circuito."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """A chamada falhou. Incrementa o erro e avalia se o circuito deve abrir."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN