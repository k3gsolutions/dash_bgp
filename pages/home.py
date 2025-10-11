import streamlit as st
from datetime import datetime

def render():
    """Renderiza a página inicial"""
    
    # Cabeçalho de boas-vindas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("🎯 Bem-vindo ao K3G Device Manager")
        st.markdown("""
        Sistema integrado para gerenciamento de dispositivos de rede, 
        geração de configurações e ferramentas de diagnóstico.
        """)
    
    with col2:
        st.image(
            "https://k3gsolutions.com.br/wp-content/uploads/2025/01/logo-monitoring-k3g-e1738253202895.png",
            width=200
        )
    
    st.divider()
    
    # Cards de funcionalidades
    st.subheader("📚 Funcionalidades Principais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📝 Cadastro
        - Gerenciar clientes
        - Configurar sites
        - Registrar dispositivos
        - Cadastrar circuitos
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 Consulta
        - Buscar informações de clientes
        - Consultar dispositivos
        - Visualizar configurações
        - Histórico de mudanças
        """)
    
    with col3:
        st.markdown("""
        ### ⚙️ Configuração
        - Gerar configs automaticamente
        - Templates personalizados
        - Validação de sintaxe
        - Export para dispositivos
        """)
    
    st.divider()
    
    # Estatísticas (exemplo)
    st.subheader("📊 Visão Geral do Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Clientes Ativos", "127", delta="5")
    
    with col2:
        st.metric("Dispositivos", "1,543", delta="12")
    
    with col3:
        st.metric("Sites", "89", delta="-2")
    
    with col4:
        st.metric("Configs Geradas", "2,456", delta="234")
    
    st.divider()
    
    # Informações do sistema
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Última Sincronização**  
        {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """)
    
    with col2:
        st.success("""
        **Status do Sistema**  
        ✅ Todos os serviços operacionais
        """)