import streamlit as st
from streamlit_tree_select import tree_select
from services.netbox_service import NetboxService
from services.template_service import TemplateService
from components.service_tree import ServiceTreeBuilder
from components.config_forms import ConfigForms
import base64

def render():
    """Renderiza a página de geração de configurações"""
    
    st.title("⚙️ Gerador de Configurações de Rede")
    st.markdown("Selecione o tipo de serviço e preencha os dados para gerar a configuração")
    
    # Inicializar serviços
    netbox = NetboxService()
    template_service = TemplateService()
    forms = ConfigForms()
    
    # Obter o tenant selecionado da sessão
    from core.session_state import SessionStateManager
    state = SessionStateManager()
    
    selected_tenant_id = state.get('selected_tenant_id')
    selected_tenant_name = state.get('selected_tenant_name')
    
    if not selected_tenant_id or selected_tenant_id == "< Selecione o Cliente >":
        st.info("👈 Por favor, selecione um cliente na barra lateral para continuar")
        
        # Exibir informações úteis
        with st.expander("ℹ️ Informações sobre Geração de Configurações"):
            st.markdown("""
            ### Como usar o Gerador de Configurações
            
            1. **Selecione um Cliente** na barra lateral
            2. **Escolha o tipo de serviço** na árvore de serviços
            3. **Preencha o formulário** com as informações necessárias
            4. **Gere a configuração** e faça o download
            
            ### Serviços Disponíveis
            
            #### L2VPN
            - **VLAN**: Configuração de VLAN em um dispositivo
            - **Point-to-Point**: Conexão L2 entre dois sites
            - **Point-to-Multipoint**: VPLS conectando múltiplos sites
            
            #### L3VPN
            - **Cliente Dedicado**: Configuração de enlace L3 dedicado
            - **Cliente de Trânsito**: Peering BGP para cliente de trânsito
            - **Upstream/Operadora**: Peering BGP com operadora
            - **Peering CDN**: Configuração de peering com CDN
            - **Peering IX**: Configuração para IX (Internet Exchange)
            """)
        
        return
    
    # Buscar sites do tenant
    with st.spinner(f"Carregando sites de {selected_tenant_name}..."):
        tenant_sites = netbox.get_sites(tenant_id=selected_tenant_id)
    
    if not tenant_sites:
        st.warning(f"⚠️ Nenhum site encontrado para o cliente {selected_tenant_name}")
        st.info("Cadastre sites para este cliente no Netbox antes de gerar configurações.")
        return
    
    # Obter o serviço selecionado do estado da sessão
    from core.session_state import SessionStateManager
    state_manager = SessionStateManager()
    selected_service_dict = {"checked": [state_manager.get('selected_service')]} if state_manager.get('selected_service') else None
    
    # Verificar se algum serviço foi selecionado
    if not selected_service_dict or not selected_service_dict.get("checked"):
        st.info("👈 Selecione um tipo de serviço na árvore ao lado para começar")
        
        # Mostrar estatísticas do cliente
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cliente Selecionado", selected_tenant_name)
        
        with col2:
            st.metric("Total de Sites", len(tenant_sites))
        
        with col3:
            devices = netbox.get_devices(tenant_id=selected_tenant_id)
            st.metric("Total de Dispositivos", len(devices))
        
        st.divider()
        
        # Listar sites disponíveis
        st.subheader("📍 Sites Disponíveis")
        
        for site in tenant_sites:
            with st.expander(f"{site['name']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {site['id']}")
                    st.write(f"**Slug:** {site.get('slug', 'N/A')}")
                
                with col2:
                    status = site.get('status', {})
                    st.write(f"**Status:** {status.get('label', 'N/A') if status else 'N/A'}")
                    
                    region = site.get('region', {})
                    st.write(f"**Região:** {region.get('name', 'N/A') if region else 'N/A'}")
        
        return
    
    service_value = selected_service_dict["checked"][0]
    
    # Header com informações do serviço selecionado
    st.info(f"📌 Serviço Selecionado: **{service_value.upper().replace('-', ' ').replace('_', ' ')}**")
    st.divider()
    
    # Renderizar formulário apropriado
    config_data = None
    
    try:
        if service_value == "l2vpn-vlan":
            config_data = forms.render_l2vpn_vlan_form(tenant_sites)
        
        elif service_value == "l2vpn-ptp":
            config_data = forms.render_l2vpn_ptp_form(tenant_sites)
        
        elif service_value == "l2vpn-ptmp":
            st.warning("⚠️ Formulário L2VPN Point-to-Multipoint ainda não implementado")
            st.info("Este serviço está em desenvolvimento. Em breve estará disponível!")
            return
        
        elif service_value == "cl_dedicado":
            st.warning("⚠️ Formulário Cliente Dedicado ainda não implementado")
            st.info("Este serviço está em desenvolvimento. Em breve estará disponível!")
            return
        
        elif service_value == "bgp_cl_trans":
            config_data = forms.render_bgp_form("cliente_transito", tenant_sites)
        
        elif service_value == "bgp_ups":
            config_data = forms.render_bgp_form("upstream", tenant_sites)
        
        elif service_value == "bgp_ups_comm":
            config_data = forms.render_bgp_form("upstream_comm", tenant_sites)
        
        elif service_value == "peering_cdn_comm":
            config_data = forms.render_bgp_form("cdn_comm", tenant_sites)
        
        elif service_value == "bgp_ixbr_comm":
            config_data = forms.render_bgp_form("ixbr_comm", tenant_sites)
        
        else:
            st.warning(f"⚠️ Formulário para '{service_value}' ainda não implementado")
            st.info("Este serviço está em desenvolvimento. Em breve estará disponível!")
            return
    
    except Exception as e:
        st.error(f"❌ Erro ao renderizar formulário: {str(e)}")
        with st.expander("🔍 Detalhes do Erro"):
            st.exception(e)
        return
    
    # Gerar e exibir configuração
    if config_data:
        st.divider()
        st.subheader("📄 Configuração Gerada")
        
        try:
            # Determinar template path baseado no tipo de serviço
            template_map = {
                "l2vpn-vlan": "template/l2vpn/vlan",
                "l2vpn-ptp": "template/l2vpn/ptp",
                "l2vpn-ptmp": "template/l2vpn/ptmp",
                "cl_dedicado": "template/l3vpn/cl_ded",
                "bgp_cl_trans": "template/l3vpn/cl_trans_ip",
                "bgp_ups": "template/l3vpn/bgp_ups",
                "bgp_ups_comm": "template/l3vpn/bgp_ups_comm",
                "peering_cdn_comm": "template/l3vpn/peering_cdn_comm",
                "bgp_ixbr_comm": "template/l3vpn/bgp_ixbr_comm",
            }
            
            template_path = template_map.get(service_value)
            
            if not template_path:
                st.error(f"❌ Template não encontrado para o serviço '{service_value}'")
                return
            
            # Preparar dados para o template
            template_data = config_data.copy()
            
            # Para L2VPN VLAN, buscar nome do dispositivo
            if service_value == "l2vpn-vlan":
                try:
                    device = netbox.get_device_by_id(config_data["selected_device"])
                    template_data["device_name"] = device["name"]
                except Exception as e:
                    st.warning(f"⚠️ Não foi possível buscar o nome do dispositivo: {str(e)}")
                    template_data["device_name"] = f"Device-{config_data['selected_device']}"
            
            # Renderizar template
            with st.spinner("Gerando configuração..."):
                config_output = template_service.render_template(template_path, **template_data)
            
            # Exibir resultado
            st.success("✅ Configuração gerada com sucesso!")
            
            # Tabs para visualização
            tab_config, tab_preview, tab_summary = st.tabs([
                "📄 Configuração Completa", 
                "👁️ Preview", 
                "📊 Resumo"
            ])
            
            with tab_config:
                st.code(config_output, language="bash", line_numbers=True)
                
                # Botão de download
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    filename = generate_filename(service_value, config_data)
                    st.download_button(
                        label="📥 Download TXT",
                        data=config_output,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    if st.button("📋 Copiar para Clipboard", use_container_width=True):
                        st.toast("✅ Copiado para a área de transferência!", icon="✅")
                
                st.info(f"💾 Arquivo: `{filename}`")
            
            with tab_preview:
                render_config_preview(config_output, config_data, service_value)
            
            with tab_summary:
                render_config_summary(config_data, service_value)
        
        except Exception as e:
            st.error(f"❌ Erro ao gerar configuração: {str(e)}")
            with st.expander("🔍 Detalhes do Erro"):
                st.exception(e)
                st.markdown("**Dados Recebidos:**")
                st.json(config_data)

def generate_filename(service_type: str, config_data: dict) -> str:
    """Gera nome do arquivo de configuração"""
    customer = config_data.get('customer_name', 'config').replace(' ', '_')
    vlan = config_data.get('vlan_id_a', config_data.get('vlan_id', ''))
    circuito = config_data.get('circuito', '')
    
    parts = [service_type, customer]
    
    if vlan:
        parts.append(f"vlan{vlan}")
    if circuito:
        parts.append(f"c{circuito}")
    
    return f"{'_'.join(parts)}.txt"

def render_config_preview(config_output: str, config_data: dict, service_type: str):
    """Renderiza preview formatado da configuração"""
    
    st.markdown("### 🎯 Comandos Principais")
    
    # Filtrar e extrair comandos principais
    lines = config_output.split('\n')
    main_commands = []
    
    for line in lines:
        stripped = line.strip()
        # Ignorar comentários e linhas vazias
        if stripped and not stripped.startswith('#') and stripped != 'quit':
            main_commands.append(stripped)
    
    if main_commands:
        # Mostrar primeiros comandos em cards
        for i, cmd in enumerate(main_commands[:15], 1):
            if cmd.startswith(('vlan', 'interface', 'bgp', 'route-policy', 'ip ')):
                st.code(cmd, language="bash")
        
        if len(main_commands) > 15:
            with st.expander(f"➕ Mostrar mais {len(main_commands) - 15} comandos"):
                for cmd in main_commands[15:]:
                    st.code(cmd, language="bash")
        
        st.metric("Total de Comandos", len(main_commands))
    else:
        st.info("Nenhum comando principal identificado")
    
    # Estatísticas
    st.divider()
    st.markdown("### 📈 Estatísticas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Linhas Totais", len(lines))
    
    with col2:
        comments = len([l for l in lines if l.strip().startswith('#')])
        st.metric("Comentários", comments)
    
    with col3:
        empty = len([l for l in lines if not l.strip()])
        st.metric("Linhas Vazias", empty)

def render_config_summary(config_data: dict, service_type: str):
    """Renderiza resumo da configuração"""
    
    st.markdown("### 📋 Informações da Configuração")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Informações Gerais**")
        st.write(f"• **Tipo de Serviço:** {service_type.upper().replace('-', ' ').replace('_', ' ')}")
        st.write(f"• **Cliente:** {config_data.get('customer_name', 'N/A')}")
        
        if config_data.get('device_name'):
            st.write(f"• **Dispositivo Principal:** {config_data.get('device_name')}")
        elif config_data.get('device_name_a'):
            st.write(f"• **Dispositivo A:** {config_data.get('device_name_a')}")
    
    with col2:
        st.markdown("**Detalhes Técnicos**")
        
        # VLANs
        if config_data.get('vlan_id_a'):
            st.write(f"• **VLAN A:** {config_data.get('vlan_id_a')}")
        if config_data.get('vlan_id_b'):
            st.write(f"• **VLAN B:** {config_data.get('vlan_id_b')}")
        if config_data.get('vlan_id'):
            st.write(f"• **VLAN:** {config_data.get('vlan_id')}")
        
        # BGP Info
        if config_data.get('asn_local'):
            st.write(f"• **ASN Local:** {config_data.get('asn_local')}")
        if config_data.get('asn_remoto'):
            st.write(f"• **ASN Remoto:** {config_data.get('asn_remoto')}")
        
        # VPLS
        if config_data.get('vpls_id'):
            st.write(f"• **VPLS ID:** {config_data.get('vpls_id')}")
    
    # Interfaces
    st.divider()
    
    if config_data.get('interfaces'):
        st.markdown("**Interfaces Configuradas**")
        interfaces = config_data.get('interfaces', [])
        
        for idx, iface in enumerate(interfaces, 1):
            if isinstance(iface, dict):
                iface_name = iface.get('name', f'Interface {idx}')
                untag = "Untagged" if iface.get('untag') else "Tagged"
                st.write(f"{idx}. **{iface_name}** - {untag}")
            else:
                st.write(f"{idx}. {iface}")
    
    # IPs de Peering
    if config_data.get('peer_local_v4') or config_data.get('peer_remoto_v4'):
        st.divider()
        st.markdown("**Endereços IP**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if config_data.get('peer_local_v4'):
                st.write(f"**Local IPv4:** {config_data.get('peer_local_v4')}/{config_data.get('peer_local_mask_v4', '')}")
            if config_data.get('peer_local_v6'):
                st.write(f"**Local IPv6:** {config_data.get('peer_local_v6')}/{config_data.get('peer_local_mask_v6', '')}")
        
        with col2:
            if config_data.get('peer_remoto_v4'):
                st.write(f"**Remoto IPv4:** {config_data.get('peer_remoto_v4')}/{config_data.get('peer_remoto_mask_v4', '')}")
            if config_data.get('peer_remoto_v6'):
                st.write(f"**Remoto IPv6:** {config_data.get('peer_remoto_v6')}/{config_data.get('peer_remoto_mask_v6', '')}")
    
    # Prefixos BGP
    if config_data.get('default_prefix_v4') or config_data.get('default_prefix_v6'):
        st.divider()
        st.markdown("**Prefixos Anunciados**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            prefixes_v4 = config_data.get('default_prefix_v4', [])
            if prefixes_v4:
                st.write(f"**IPv4:** {len(prefixes_v4)} prefixos")
                with st.expander("Ver Prefixos IPv4"):
                    for p in prefixes_v4[:10]:
                        if isinstance(p, dict):
                            st.code(f"{p.get('Prefixo')}/{p.get('Máscara')}")
                    if len(prefixes_v4) > 10:
                        st.info(f"... e mais {len(prefixes_v4) - 10} prefixos")
        
        with col2:
            prefixes_v6 = config_data.get('default_prefix_v6', [])
            if prefixes_v6:
                st.write(f"**IPv6:** {len(prefixes_v6)} prefixos")
                with st.expander("Ver Prefixos IPv6"):
                    for p in prefixes_v6[:10]:
                        if isinstance(p, dict):
                            st.code(f"{p.get('Prefixo')}/{p.get('Máscara')}")
                    if len(prefixes_v6) > 10:
                        st.info(f"... e mais {len(prefixes_v6) - 10} prefixos")
    
    # Metadados
    st.divider()
    st.caption("💡 **Dica:** Sempre revise a configuração antes de aplicá-la no dispositivo")