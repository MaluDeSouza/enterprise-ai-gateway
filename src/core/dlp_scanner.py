import re
import base64
import fitz

class DLPScanner:
    def __init__(self):
        # Padrões de Nível 1: Identificação direta via Regex agrupada
        self.patterns = {
            "cpf": re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'),
            "cartao_credito": re.compile(r'\b(?:\d[ -]*?){13,16}\b'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'),
            "cep": re.compile(r'\b\d{5}-?\d{3}\b'),
            "cnh": re.compile(r'\b\d{11}\b'),
            "titulo_eleitor": re.compile(r'\b\d{12}\b'),
            "rg_padrao": re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}-?[0-9X|x]\b')
        }

    def has_pii(self, text: str) -> bool:
        """Varre o texto puro em busca de PII iterando sobre todos os padrões."""
        if not text:
            return False
            
        # O pulo do gato: varremos todos os valores do dicionário dinamicamente
        for pattern in self.patterns.values():
            if pattern.search(text):
                return True
                
        return False

    def scan_pdf_b64(self, b64_string: str) -> bool:
        """Decodifica o Base64, abre o PDF na RAM, extrai o texto e varre."""
        if not b64_string:
            return False
            
        try:
            # 1. Decodifica a string de volta para bytes
            pdf_bytes = base64.b64decode(b64_string)
            
            # 2. Abre o PDF na memória (sem IO de disco)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # 3. Extrai e concatena o texto de todas as páginas
            full_text = ""
            for page in doc:
                full_text += page.get_text()
                
            # 4. Passa o texto extraído no nosso Cão de Guarda dinâmico
            return self.has_pii(full_text)
            
        except Exception as e:
            # Fail-safe: se o arquivo estiver corrompido, bloqueamos por segurança
            print(f"Erro ao analisar o PDF: {e}")
            return True