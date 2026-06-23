import streamlit as st
import httpx
import json

# Configuração da página
st.set_page_config(page_title="Enterprise AI Gateway", page_icon="🛰️")
st.title("🛰️ Enterprise AI Gateway")
st.markdown("Simulador de Front-end passando pelo nosso Proxy Reverso com Governança de Acesso.")

# NOVO: Campo de senha de verdade na barra lateral!
api_key = st.sidebar.text_input("🔑 Digite sua Chave API", type="password", help="Ex: premium-key-123")
st.sidebar.markdown("*Dica: Tente usar `premium-key-123` ou `free-key-456`*")

# Histórico de chat na tela
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# Caixa de texto para o usuário digitar
if prompt := st.chat_input("Faça uma pergunta para a IA..."):
    
    # Trava de segurança no próprio front-end
    if not api_key:
        st.error("⚠️ Por favor, digite sua Chave API na barra lateral antes de enviar a mensagem!")
        st.stop()

    # Adiciona a pergunta na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Prepara o balão de resposta da IA
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # O payload exato que nosso Gateway espera (agora sem o tenant_tier falso)
        payload = {
            "model": "gpt-4", 
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # NOVO: A nossa Aduana - Enviamos a senha escondida no cabeçalho da requisição
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            # Conectando ao NOSSO Gateway com o cabeçalho de autenticação
            # Conectando ao NOSSO Gateway com o cabeçalho de autenticação
            with httpx.stream("POST", "http://127.0.0.1:8000/v1/chat/completions", json=payload, headers=headers, timeout=120.0) as response:
                
                # Se o Gateway barrar a senha (Erro 401 Unauthorized ou 403 Forbidden)
                if response.status_code in [401, 403]:
                    st.error("🚫 Senha incorreta ou acesso negado. Verifique sua Chave API.")
                    st.stop()
                    
                # Caso seja outro erro do servidor (ex: 500)
                elif response.status_code != 200:
                    response.read() # Lê o erro preso no stream
                    try:
                        error_detail = response.json().get("detail", f"Erro no servidor: {response.status_code}")
                    except:
                        error_detail = f"Erro no servidor: {response.status_code}"
                        
                    st.error(f"⚠️ {error_detail}")
                    st.stop()
                    
                # Se a senha estiver correta, lê o stream da IA
                for line in response.iter_lines():
                    if line and line.startswith("data: "):
                        chunk_str = line[6:]
                        if chunk_str == "[DONE]":
                            break
                        
                        try:
                            # Lemos o JSON blindado
                            chunk_json = json.loads(chunk_str)
                            
                            # CUIDADO AQUI: 'choices' é uma lista!
                            chunk_real = chunk_json["choices"][0]["delta"].get("content", "")
                            
                            full_response += chunk_real
                            message_placeholder.markdown(full_response + "▌")
                        except Exception:
                            # Ignora sujeiras na rede
                            continue
            
            # Tira o cursor piscante no final
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"O Gateway está offline ou falhou: {e}")