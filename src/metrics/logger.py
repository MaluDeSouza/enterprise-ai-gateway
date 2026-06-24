import logging
import structlog

def setup_logger():
    """Configura o motor de logs estruturados em JSON."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Redireciona o logging padrão do Python para o structlog
    logging.basicConfig(format="%(message)s", level=logging.INFO)

def get_logger(name: str):
    return structlog.get_logger(name)