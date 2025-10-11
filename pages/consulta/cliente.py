import streamlit as st
from services.netbox_service import NetboxService

def render():
    """Renderiza a página de consulta de cliente"""
    st.title("👤 Consulta de Cliente")
    
    service = NetboxService()
    
    # Buscar clientes
    with st.spinner("Carregando clientes..."):
        tenants = service.get_tenants()
    
    if not tenants:
        st.warning("Nenhum cliente encontrado no sistema")
        return
    
    # Seletor de cliente
    tenant_options = {t['id']: t['name'] for t in tenants}
    selected_id = st.selectbox(
        "Selecione o Cliente",
        options=list(tenant_options.keys()),
        format_func=lambda x: tenant_options[x]
    )
    
    if selected_id:
        tenant = service.get_tenant_by_id(selected_id)
        
        if tenant:
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Informações Gerais")
                st.write(f"**ID:** {tenant.get('id')}")
                st.write(f"**Nome:** {tenant.get('name')}")
                st.write(f"**Slug:** {tenant.get('slug', 'N/A')}")
            
            with col2:
                st.subheader("Detalhes")
                st.write(f"**Descrição:** {tenant.get('description', 'N/A')}")
                st.write(f"**Criado em:** {tenant.get('created', 'N/A')}")
            
            # Buscar sites do cliente
            st.divider()
            st.subheader("Sites Vinculados")
            
            sites = service.get_sites(tenant_id=selected_id)
            
            if sites:
                for site in sites:
                    with st.expander(f"📍 {site.get('name')}"):
                        st.write(f"**ID:** {site.get('id')}")
                        st.write(f"**Status:** {site.get('status', {}).get('label', 'N/A')}")
                        st.write(f"**Região:** {site.get('region', {}).get('name', 'N/A') if site.get('region') else 'N/A'}")
            else:
                st.info("Nenhum site vinculado a este cliente")