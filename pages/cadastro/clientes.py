import streamlit as st
from services.netbox_service import NetboxService
from core.session_state import SessionStateManager

def render():
    """Renderiza a página de cadastro de clientes"""
    
    st.title("👥 Cadastro de Clientes")
    st.markdown("Gerencie os clientes cadastrados no sistema")
    
    # Tabs para organizar cadastro e listagem
    tab_list, tab_new = st.tabs(["📋 Listar Clientes", "➕ Novo Cliente"])
    
    with tab_list:
        _render_client_list()
    
    with tab_new:
        _render_new_client_form()

def _render_client_list():
    """Renderiza a lista de clientes"""
    
    st.subheader("Clientes Cadastrados")
    
    # Barra de busca
    search = st.text_input("🔍 Buscar cliente", placeholder="Digite o nome do cliente...")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            SessionStateManager.clear_cache()
            st.rerun()
    
    # Aqui você carregaria os clientes do Netbox
    # Por enquanto, exemplo estático
    with st.expander("Cliente Exemplo 1", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**ID:** 001")
            st.write("**Nome:** Cliente Teste")
        with col2:
            st.write("**Sites:** 5")
            st.write("**Status:** Ativo")
        
        if st.button("✏️ Editar", key="edit_1"):
            st.info("Funcionalidade em desenvolvimento")

def _render_new_client_form():
    """Renderiza o formulário de novo cliente"""
    
    st.subheader("Adicionar Novo Cliente")
    
    with st.form("new_client_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome do Cliente *", placeholder="Ex: Empresa XYZ")
            cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
        
        with col2:
            email = st.text_input("E-mail de Contato", placeholder="contato@empresa.com")
            telefone = st.text_input("Telefone", placeholder="(00) 0000-0000")
        
        descricao = st.text_area("Descrição", placeholder="Informações adicionais sobre o cliente...")
        
        ativo = st.checkbox("Cliente Ativo", value=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submitted = st.form_submit_button("💾 Salvar", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submitted:
            if nome:
                # Aqui você salvaria no Netbox
                st.success(f"✅ Cliente '{nome}' cadastrado com sucesso!")
            else:
                st.error("❌ O nome do cliente é obrigatório")
        
        if cancelled:
            st.rerun()