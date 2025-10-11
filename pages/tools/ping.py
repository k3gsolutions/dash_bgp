import streamlit as st
import subprocess
from datetime import datetime

def render():
    """Renderiza a ferramenta de ping"""
    
    st.title("📡 Ping Tool")
    st.markdown("Execute ping para testar conectividade com hosts")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        target = st.text_input(
            "🎯 Host de Destino",
            placeholder="Ex: 8.8.8.8 ou google.com",
            help="Endereço IP ou nome do host"
        )
    
    with col2:
        count = st.number_input("Número de Pacotes", min_value=1, max_value=100, value=4)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Executar Ping", use_container_width=True, type="primary"):
            if target:
                _execute_ping(target, count)
            else:
                st.warning("⚠️ Por favor, informe um host de destino")
    
    with col2:
        if st.button("🗑️ Limpar Resultado", use_container_width=True):
            if 'ping_result' in st.session_state:
                del st.session_state['ping_result']
            st.rerun()
    
    # Exibe resultado se existir
    if 'ping_result' in st.session_state:
        st.divider()
        st.subheader("📊 Resultado")
        st.code(st.session_state['ping_result'], language="bash")

def _execute_ping(target: str, count: int):
    """Executa o comando ping"""
    
    with st.spinner(f"Executando ping para {target}..."):
        try:
            # Comando ping (ajuste para Windows se necessário)
            cmd = ["ping", "-c", str(count), target]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = f"# Ping executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            output += f"# Comando: {' '.join(cmd)}\n\n"
            output += result.stdout
            
            if result.returncode != 0:
                output += f"\n\nErro: {result.stderr}"
            
            st.session_state['ping_result'] = output
            
            if result.returncode == 0:
                st.success("✅ Ping executado com sucesso!")
            else:
                st.error("❌ Falha na execução do ping")
                
        except subprocess.TimeoutExpired:
            st.error("❌ Timeout: O comando demorou muito para executar")
        except Exception as e:
            st.error(f"❌ Erro ao executar ping: {str(e)}")