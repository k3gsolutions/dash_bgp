import streamlit as st
from config.settings import AppConfig, MenuItem
from core.session_state import SessionStateManager

class Sidebar:
    """Gerencia a renderização da sidebar"""
    
    def __init__(self):
        self.config = AppConfig()
        self.state = SessionStateManager()
    
    def render(self):
        """Renderiza a sidebar completa"""
        with st.sidebar:
            self._render_header()
            self._render_menu()
            self._render_footer()
    
    def _render_header(self):
        """Renderiza o cabeçalho da sidebar"""
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(
                "https://k3gsolutions.com.br/wp-content/uploads/2025/01/logo-monitoring-k3g-e1738253202895.png",
                width=50
            )
        
        with col2:
            if self.state.get('sidebar_expanded'):
                st.markdown("### K3G Manager")
        
        st.divider()
    
    def _render_menu(self):
        """Renderiza o menu de navegação"""
        # Renderiza os itens do menu
        for i, item in enumerate(self.config.MENU_STRUCTURE):
            self._render_menu_item(item)
            
            # Após o botão "Gerar Configuração", adiciona o seletor de tenant
            if item.id == "gera_config" and self.state.get('current_page') == "gera_config":
                self._render_tenant_selector()
    
    def _render_menu_item(self, item: MenuItem, level: int = 0):
        """Renderiza um item do menu recursivamente"""
        indent = "  " * level
        
        if item.has_children():
            # Item com submenu
            with st.expander(f"{indent}{item.icon} {item.label}", expanded=False):
                for child in item.children:
                    self._render_menu_item(child, level + 1)
        else:
            # Item clicável
            if st.button(
                f"{indent}{item.icon} {item.label}",
                key=f"menu_{item.id}",
                use_container_width=True,
                type="primary" if self.state.get('current_page') == item.page else "secondary"
            ):
                self.state.set('current_page', item.page)
                st.rerun()
    
    def _render_tenant_selector(self):
        """Renderiza o seletor de tenant (cliente) na sidebar"""
        from services.netbox_service import NetboxService
        
        #st.markdown("---")
        st.subheader("📋 Seleção de Cliente")
        
        # Inicializar serviço do Netbox
        netbox = NetboxService()
        
        # Buscar tenants
        with st.spinner("Carregando clientes..."):
            tenants = netbox.get_tenants()
        
        if not tenants:
            st.error("❌ Nenhum tenant encontrado")
            return
        
        tenant_options = {tenant["id"]: tenant["name"] for tenant in tenants}
        tenant_list = ["< Selecione o Cliente >"] + list(tenant_options.keys())
        
        selected_tenant_id = st.selectbox(
            "Cliente",
            options=tenant_list,
            format_func=lambda x: tenant_options[x] if x in tenant_options else x,
            key="tenant_selector_main"
        )
        
        # Armazenar o tenant selecionado no estado da sessão
        if selected_tenant_id != "< Selecione o Cliente >":
            self.state.set('selected_tenant_id', selected_tenant_id)
            self.state.set('selected_tenant_name', tenant_options[selected_tenant_id])
    
    def _render_footer(self):
        """Renderiza o rodapé da sidebar"""
        st.divider()
        
        if self.state.get('sidebar_expanded'):
            st.caption("© 2025 K3G Solutions")
            st.caption("v1.0.0")