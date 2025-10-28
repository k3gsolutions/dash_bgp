import streamlit as st
from core.session_state import SessionStateManager
from core.sidebar import Sidebar
from core.navigation import PageRouter

# Importar páginas
from pages import home
from pages.cadastro import clientes, sites, dispositivos, circuitos
from pages.consulta import cliente, dispositivo
from pages.gera_config import config_generator
from pages.tools import config_analyzer, ping, traceroute, whois, looking_glass, ipcalc

# Configuração da página
st.set_page_config(
    page_title="K3G Device Manager",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhor aparência
st.markdown("""
<style>
    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilizar botões da sidebar */
    .stButton button {
        text-align: left;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateX(5px);
    }
    
    /* Estilizar expanders */
    .streamlit-expanderHeader {
        font-weight: 600;
        border-radius: 8px;
    }
    
    /* Melhorar espaçamento */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Função principal da aplicação"""
    
    # Inicializar estado da sessão
    SessionStateManager.initialize()
    
    # Criar roteador de páginas
    router = PageRouter()
    
    # Registrar todas as páginas
    router.register('home', home.render)
    router.register('cadastro.clientes', clientes.render)
    router.register('cadastro.sites', sites.render)
    router.register('cadastro.dispositivos', dispositivos.render)
    router.register('cadastro.circuitos', circuitos.render)
    router.register('consulta.cliente', cliente.render)
    router.register('consulta.dispositivo', dispositivo.render)
    router.register('gera_config', config_generator.render)
    router.register('tools.ping', ping.render)
    router.register('tools.traceroute', traceroute.render)
    router.register('tools.whois', whois.render)
    router.register('tools.looking_glass', looking_glass.render)
    router.register('tools.ipcalc', ipcalc.render)
    router.register('tools.config_analyzer', config_analyzer.render)
    
    # Renderizar sidebar
    sidebar = Sidebar()
    sidebar.render()
    
    # Renderizar página atual
    router.render_current_page()

if __name__ == "__main__":
    main()