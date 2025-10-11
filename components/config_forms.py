import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
import re
import requests
import ipaddress
from services.netbox_service import NetboxService

class ConfigForms:
    """Gerencia todos os formulários de configuração com lógica completa"""
    
    def __init__(self):
        self.netbox = NetboxService()
    
    # Padrões de validação
    IPV4_PATTERN = r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
    IPV6_PATTERN = r"([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}|::([0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:)*::([0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}|::"
    
    def _init_session_state(self):
        """Inicializa estado da sessão"""
        if 'ipv4_prefixes_data' not in st.session_state:
            st.session_state['ipv4_prefixes_data'] = []
        if 'ipv6_prefixes_data' not in st.session_state:
            st.session_state['ipv6_prefixes_data'] = []

    def _validate_customer_name(self, customer_name: str) -> bool:
        """Valida o nome do cliente"""
        if not customer_name:
            return False
        return customer_name.startswith(('CL-', 'AS'))

    def _lookup_asn_info(self, asn: str) -> Dict[str, Any]:
        """
        Busca informações completas do ASN incluindo prefixos
        
        Args:
            asn: ASN (com ou sem prefixo AS)
            
        Returns:
            Dict com informações do ASN e prefixos
        """
        try:
            if asn.startswith("AS"):
                asn_num = asn[2:]
            else:
                asn_num = asn
            
            # Informações básicas do ASN
            url_overview = f"https://stat.ripe.net/data/as-overview/data.json?resource={asn_num}"
            response_overview = requests.get(url_overview, timeout=10)
            
            asn_info = {
                "holder": "",
                "country": "",
                "ipv4_prefixes": [],
                "ipv6_prefixes": [],
                "success": False
            }
            
            if response_overview.status_code == 200:
                data_overview = response_overview.json()
                asn_data = data_overview.get("data", {})
                asn_info["holder"] = asn_data.get("holder", "")
                asn_info["country"] = asn_data.get("country", "")
                asn_info["success"] = True
            
            # Buscar prefixos anunciados pelo ASN
            url_prefixes = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn_num}"
            response_prefixes = requests.get(url_prefixes, timeout=15)
            
            if response_prefixes.status_code == 200:
                data_prefixes = response_prefixes.json()
                prefixes = data_prefixes.get("data", {}).get("prefixes", [])
                
                # Separar IPv4 e IPv6
                for prefix_info in prefixes:
                    prefix = prefix_info.get("prefix", "")
                    
                    if ":" in prefix:
                        # IPv6
                        asn_info["ipv6_prefixes"].append(prefix)
                    else:
                        # IPv4
                        asn_info["ipv4_prefixes"].append(prefix)
            
            return asn_info
            
        except requests.RequestException as e:
            st.error(f"Erro de rede ao buscar ASN: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            st.error(f"Erro ao processar dados do ASN: {str(e)}")
            return {"success": False, "error": str(e)}

    def _lookup_multiple_asns(self, asn_local: str, asn_remoto: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Busca informações de múltiplos ASNs
        
        Args:
            asn_local: ASN local
            asn_remoto: ASN remoto
            
        Returns:
            Tupla com (info_local, info_remoto)
        """
        info_local = self._lookup_asn_info(asn_local)
        info_remoto = self._lookup_asn_info(asn_remoto)
        
        return info_local, info_remoto

    def _render_device_selection(self, tenant_sites: List[Dict]) -> Optional[Tuple[int, int, int]]:
        """Renderiza seleção de dispositivo comum"""
        st.markdown("### 🖥️ Seleção de Dispositivo")
        
        site_dict = {site["id"]: site["name"] for site in tenant_sites}
        selected_site = st.selectbox(
            "Site *",
            options=list(site_dict.keys()),
            format_func=lambda sid: site_dict[sid],
            key="device_site"
        )
        
        site_devices = self.netbox.get_devices(site_id=selected_site)
        
        if not site_devices:
            st.warning("⚠️ Nenhum dispositivo encontrado neste site")
            return None
        
        col1, col2 = st.columns([0.75, 0.25])
        
        with col1:
            device_dict = {d["id"]: d["name"] for d in site_devices}
            selected_device = st.selectbox(
                "Dispositivo *",
                options=list(device_dict.keys()),
                format_func=lambda did: device_dict[did],
                key="selected_device"
            )
        
        with col2:
            vlan_id = st.number_input(
                "VLAN ID *",
                min_value=2,
                max_value=4094,
                value=100,
                step=1,
                key="vlan_id"
            )
        
        if selected_device:
            interfaces = self.netbox.get_device_interfaces(selected_device)
            
            if interfaces:
                interface_dict = {iface["id"]: iface["name"] for iface in interfaces}
                selected_interface = st.selectbox(
                    "Interface *",
                    options=list(interface_dict.keys()),
                    format_func=lambda iid: interface_dict[iid],
                    key="selected_interface"
                )
                
                return selected_device, vlan_id, selected_interface
        
        return None

    def _render_peer_info_section(self) -> Optional[Dict[str, str]]:
        """Renderiza seção de informações do peer"""
        st.markdown("### 🔗 Informações do Peer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            peer_ip_v4 = st.text_input(
                "Peer IPv4",
                placeholder="192.168.1.1",
                key="peer_ip_v4"
            )
        
        with col2:
            peer_ip_v6 = st.text_input(
                "Peer IPv6",
                placeholder="2001:db8::1",
                key="peer_ip_v6"
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            local_ip_v4 = st.text_input(
                "Local IPv4",
                placeholder="192.168.1.2",
                key="local_ip_v4"
            )
        
        with col4:
            local_ip_v6 = st.text_input(
                "Local IPv6", 
                placeholder="2001:db8::2",
                key="local_ip_v6"
            )
        
        # Validações básicas
        if peer_ip_v4 or peer_ip_v6 or local_ip_v4 or local_ip_v6:
            return {
                "peer_ip_v4": peer_ip_v4,
                "peer_ip_v6": peer_ip_v6,
                "local_ip_v4": local_ip_v4,
                "local_ip_v6": local_ip_v6
            }
        
        return None

    def _render_asn_and_prefixes_section(self, service_type: str) -> Tuple[str, str, str, List[str], List[str]]:
        """
        Renderiza seção de ASN e busca automática de prefixos
        
        Returns:
            Tupla com (asn_local, asn_remoto, asn_name, ipv4_prefixes, ipv6_prefixes)
        """
        st.markdown("### 🌐 Configuração de ASN")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            asn_local = st.text_input(
                "ASN Local *",
                placeholder="AS64512",
                help="ASN do seu roteador",
                key=f"asn_local_{service_type}"
            )
        
        with col2:
            asn_remoto = st.text_input(
                "ASN Remoto *", 
                placeholder="AS64513",
                help="ASN do peer remoto",
                key=f"asn_remoto_{service_type}"
            )
        
        # Inicializar variáveis de retorno
        asn_name = ""
        ipv4_prefixes = []
        ipv6_prefixes = []
        
        # Botão para buscar informações dos ASNs
        if asn_local and asn_remoto and st.button("🔍 Buscar Informações e Prefixos dos ASNs", key=f"lookup_asns_{service_type}"):
            
            # Mostrar spinner durante a busca
            with st.spinner("Buscando informações dos ASNs e prefixos..."):
                info_local, info_remoto = self._lookup_multiple_asns(asn_local, asn_remoto)
                
                # Salvar informações na sessão
                st.session_state[f'asn_local_info_{service_type}'] = info_local
                st.session_state[f'asn_remoto_info_{service_type}'] = info_remoto
                
                if info_local.get("success"):
                    st.success(f"✅ **ASN Local encontrado:** {info_local.get('holder', 'N/A')}")
                    if info_local.get('ipv4_prefixes'):
                        st.info(f"📡 **IPv4 Prefixos (Local):** {len(info_local['ipv4_prefixes'])} encontrados")
                    if info_local.get('ipv6_prefixes'):
                        st.info(f"🌐 **IPv6 Prefixos (Local):** {len(info_local['ipv6_prefixes'])} encontrados")
                else:
                    st.warning("⚠️ Não foi possível obter informações do ASN Local")
                
                if info_remoto.get("success"):
                    st.success(f"✅ **ASN Remoto encontrado:** {info_remoto.get('holder', 'N/A')}")
                    if info_remoto.get('ipv4_prefixes'):
                        st.info(f"📡 **IPv4 Prefixos (Remoto):** {len(info_remoto['ipv4_prefixes'])} encontrados")
                    if info_remoto.get('ipv6_prefixes'):
                        st.info(f"🌐 **IPv6 Prefixos (Remoto):** {len(info_remoto['ipv6_prefixes'])} encontrados")
                else:
                    st.warning("⚠️ Não foi possível obter informações do ASN Remoto")
        
        # Exibir informações salvas na sessão
        info_local = st.session_state.get(f'asn_local_info_{service_type}', {})
        info_remoto = st.session_state.get(f'asn_remoto_info_{service_type}', {})
        
        if info_remoto.get("success"):
            asn_name = info_remoto.get("holder", "")
            if asn_name:
                st.info(f"**ASN Remoto:** {asn_name}")
        
        # Seção de seleção de prefixos
        if info_local.get("success") or info_remoto.get("success"):
            st.markdown("### 📊 Seleção de Prefixos")
            
            # Determinar qual ASN usar para prefixos baseado no tipo de serviço
            if service_type in ["cliente_transito", "bgp_cl_trans"]:
                # Para cliente de trânsito, usar prefixos do ASN remoto (cliente)
                source_info = info_remoto
                source_label = "Remoto (Cliente)"
            else:
                # Para outros tipos, usar ASN local
                source_info = info_local
                source_label = "Local"
            
            st.info(f"ℹ️ **Usando prefixos do ASN {source_label}**")
            
            # IPv4 Prefixes
            if source_info.get('ipv4_prefixes'):
                st.markdown("#### 📡 Prefixos IPv4 Disponíveis")
                
                # Checkbox para selecionar todos
                select_all_ipv4 = st.checkbox(
                    f"Selecionar todos os {len(source_info['ipv4_prefixes'])} prefixos IPv4",
                    key=f"select_all_ipv4_{service_type}"
                )
                
                if select_all_ipv4:
                    selected_ipv4 = source_info['ipv4_prefixes']
                    st.session_state[f'ipv4_prefixes_data_{service_type}'] = selected_ipv4
                    
                    # Mostrar prefixos selecionados em um expander
                    with st.expander(f"Ver {len(selected_ipv4)} prefixos IPv4 selecionados"):
                        for prefix in selected_ipv4:
                            st.code(prefix)
                else:
                    # Multiselect para seleção manual
                    selected_ipv4 = st.multiselect(
                        "Selecione os prefixos IPv4 desejados:",
                        source_info['ipv4_prefixes'],
                        key=f"selected_ipv4_{service_type}"
                    )
                    st.session_state[f'ipv4_prefixes_data_{service_type}'] = selected_ipv4
                
                ipv4_prefixes = st.session_state.get(f'ipv4_prefixes_data_{service_type}', [])
            
            # IPv6 Prefixes
            if source_info.get('ipv6_prefixes'):
                st.markdown("#### 🌐 Prefixos IPv6 Disponíveis")
                
                # Checkbox para selecionar todos
                select_all_ipv6 = st.checkbox(
                    f"Selecionar todos os {len(source_info['ipv6_prefixes'])} prefixos IPv6",
                    key=f"select_all_ipv6_{service_type}"
                )
                
                if select_all_ipv6:
                    selected_ipv6 = source_info['ipv6_prefixes']
                    st.session_state[f'ipv6_prefixes_data_{service_type}'] = selected_ipv6
                    
                    # Mostrar prefixos selecionados em um expander
                    with st.expander(f"Ver {len(selected_ipv6)} prefixos IPv6 selecionados"):
                        for prefix in selected_ipv6:
                            st.code(prefix)
                else:
                    # Multiselect para seleção manual
                    selected_ipv6 = st.multiselect(
                        "Selecione os prefixos IPv6 desejados:",
                        source_info['ipv6_prefixes'],
                        key=f"selected_ipv6_{service_type}"
                    )
                    st.session_state[f'ipv6_prefixes_data_{service_type}'] = selected_ipv6
                
                ipv6_prefixes = st.session_state.get(f'ipv6_prefixes_data_{service_type}', [])
        
        return asn_local, asn_remoto, asn_name, ipv4_prefixes, ipv6_prefixes

    def render_l2vpn_vlan_form(self, tenant_sites: List[Dict]) -> Optional[Dict[str, Any]]:
        """Formulário para L2VPN VLAN"""
        st.markdown("## 🔧 Configuração L2VPN - VLAN")
        st.markdown("---")
        
        # Nome do cliente
        customer_name = st.text_input(
            "Nome do Cliente *",
            placeholder="CL-FULANO_DE_TAL ou AS1234-FULANO_DE_TAL",
            help="Nome deve começar com CL- ou AS"
        )
        
        if not self._validate_customer_name(customer_name):
            st.warning("⚠️ Nome do cliente deve começar com 'CL-' ou 'AS'")
            return None
        
        # Seleção de dispositivo
        device_selection = self._render_device_selection(tenant_sites)
        if not device_selection:
            return None
        
        selected_device, vlan_id, selected_interface = device_selection
        
        # Circuito (opcional)
        show_circuito = st.checkbox("Adicionar informações de circuito", value=False)
        circuito = None
        if show_circuito:
            circuito = st.text_input(
                "Circuito/Tag",
                placeholder="Ex: CIRCUITO-12345",
                help="Informação adicional sobre o circuito"
            )
        
        # Botão para gerar configuração
        if st.button("🎯 Gerar Configuração L2VPN VLAN", type="primary"):
            return {
                "service_type": "l2vpn_vlan",
                "customer_name": customer_name,
                "selected_device": selected_device,
                "vlan_id": vlan_id,
                "selected_interface": selected_interface,
                "circuito": circuito if show_circuito else None
            }
        
        return None

    def render_l2vpn_ptp_form(self, tenant_sites: List[Dict]) -> Optional[Dict[str, Any]]:
        """Formulário para L2VPN Point-to-Point"""
        st.markdown("## 🔧 Configuração L2VPN - Point to Point")
        st.markdown("---")
        
        # Nome do cliente
        customer_name = st.text_input(
            "Nome do Cliente *",
            placeholder="CL-FULANO_DE_TAL ou AS1234-FULANO_DE_TAL",
            help="Nome deve começar com CL- ou AS"
        )
        
        if not self._validate_customer_name(customer_name):
            st.warning("⚠️ Nome do cliente deve começar com 'CL-' ou 'AS'")
            return None
        
        # Site A
        st.markdown("### 📍 Site A")
        device_selection_a = self._render_device_selection(tenant_sites)
        if not device_selection_a:
            return None
        
        # Site B
        st.markdown("### 📍 Site B")
        # Duplicar lógica para Site B com keys diferentes
        site_dict = {site["id"]: site["name"] for site in tenant_sites}
        selected_site_b = st.selectbox(
            "Site B *",
            options=list(site_dict.keys()),
            format_func=lambda sid: site_dict[sid],
            key="device_site_b"
        )
        
        site_devices_b = self.netbox.get_devices(site_id=selected_site_b)
        if not site_devices_b:
            st.warning("⚠️ Nenhum dispositivo encontrado no Site B")
            return None
        
        col1, col2 = st.columns([0.75, 0.25])
        with col1:
            device_dict_b = {d["id"]: d["name"] for d in site_devices_b}
            selected_device_b = st.selectbox(
                "Dispositivo B *",
                options=list(device_dict_b.keys()),
                format_func=lambda did: device_dict_b[did],
                key="selected_device_b"
            )
        
        with col2:
            vlan_id_b = st.number_input(
                "VLAN ID B *",
                min_value=2,
                max_value=4094,
                value=200,
                step=1,
                key="vlan_id_b"
            )
        
        selected_interface_b = None
        if selected_device_b:
            interfaces_b = self.netbox.get_device_interfaces(selected_device_b)
            if interfaces_b:
                interface_dict_b = {iface["id"]: iface["name"] for iface in interfaces_b}
                selected_interface_b = st.selectbox(
                    "Interface B *",
                    options=list(interface_dict_b.keys()),
                    format_func=lambda iid: interface_dict_b[iid],
                    key="selected_interface_b"
                )
        
        if not selected_interface_b:
            return None
        
        # Botão para gerar configuração
        if st.button("🎯 Gerar Configuração L2VPN PtP", type="primary"):
            selected_device_a, vlan_id_a, selected_interface_a = device_selection_a
            
            return {
                "service_type": "l2vpn_ptp",
                "customer_name": customer_name,
                "site_a": {
                    "device": selected_device_a,
                    "vlan_id": vlan_id_a,
                    "interface": selected_interface_a
                },
                "site_b": {
                    "device": selected_device_b,
                    "vlan_id": vlan_id_b,
                    "interface": selected_interface_b
                }
            }
        
        return None

    def render_bgp_form(self, service_type: str, tenant_sites: List[Dict]) -> Optional[Dict[str, Any]]:
        """Formulário para configurações BGP com busca automática de prefixos"""
        self._init_session_state()
        
        # Títulos específicos por tipo de serviço
        titles = {
            "cliente_transito": "## 🌐 BGP Cliente de Trânsito",
            "upstream": "## 🚀 BGP Upstream/Operadora", 
            "upstream_comm": "## 🏢 BGP Upstream com Communities",
            "cdn_comm": "## 📺 Peering CDN com Communities",
            "ixbr_comm": "## 🇧🇷 Peering IX.br com Communities"
        }
        
        st.markdown(titles.get(service_type, "## 🔧 Configuração BGP"))
        st.markdown("---")
        
        # Nome do cliente
        customer_name = st.text_input(
            "Nome do Cliente *",
            placeholder="CL-FULANO_DE_TAL ou AS1234-FULANO_DE_TAL",
            help="Nome deve começar com CL- ou AS",
            key=f"customer_name_bgp_{service_type}"
        )
        
        if not self._validate_customer_name(customer_name):
            st.warning("⚠️ Nome do cliente deve começar com 'CL-' ou 'AS'")
            return None
        
        # ASN e busca automática de prefixos
        asn_local, asn_remoto, asn_name, ipv4_prefixes, ipv6_prefixes = self._render_asn_and_prefixes_section(service_type)
        
        if not asn_local or not asn_remoto:
            st.warning("⚠️ Por favor, preencha os campos ASN Local e ASN Remoto")
            return None
        
        # Seleção de dispositivo
        device_selection = self._render_device_selection(tenant_sites)
        if not device_selection:
            return None
        
        selected_device, vlan_id, selected_interface = device_selection
        
        # Informações do Peer
        peer_info = self._render_peer_info_section()
        if not peer_info:
            st.warning("⚠️ Por favor, preencha pelo menos um IP de peer (IPv4 ou IPv6)")
            return None
        
        # MD5 Authentication
        st.markdown("### 🔐 Autenticação MD5")
        check_md5 = st.checkbox("Habilitar autenticação MD5", value=False, key=f"md5_{service_type}")
        
        md5_v4 = ""
        md5_v6 = ""
        
        if check_md5:
            col1, col2 = st.columns(2)
            with col1:
                md5_v4 = st.text_input(
                    "Senha MD5 IPv4",
                    type="password",
                    help="Senha MD5 para sessão BGP IPv4",
                    key=f"md5_v4_{service_type}"
                )
            with col2:
                md5_v6 = st.text_input(
                    "Senha MD5 IPv6", 
                    type="password",
                    help="Senha MD5 para sessão BGP IPv6",
                    key=f"md5_v6_{service_type}"
                )
        
        # Circuito (opcional)
        show_circuito = st.checkbox("Adicionar informações de circuito", value=False, key=f"circuito_{service_type}")
        circuito = None
        if show_circuito:
            circuito = st.text_input(
                "Circuito/Tag",
                placeholder="Ex: CIRCUITO-12345",
                help="Informação adicional sobre o circuito",
                key=f"circuito_input_{service_type}"
            )
        
        # Validação final e botão
        has_prefixes = len(ipv4_prefixes) > 0 or len(ipv6_prefixes) > 0
        can_generate = (
            customer_name and 
            asn_local and 
            asn_remoto and 
            has_prefixes and
            peer_info
        )
        
        if not has_prefixes:
            st.warning("⚠️ Por favor, busque os ASNs e selecione pelo menos um prefixo")
        
        # Botão para gerar configuração
        if st.button("🎯 Gerar Configuração BGP", type="primary", disabled=not can_generate, key=f"generate_{service_type}"):
            result = {
                "service_type": service_type,
                "customer_name": customer_name,
                "asn_local": asn_local,
                "asn_remoto": asn_remoto,
                "asn_name": asn_name,
                "ipv4_prefixes": ipv4_prefixes,
                "ipv6_prefixes": ipv6_prefixes,
                "selected_device": selected_device,
                "vlan_id": vlan_id,
                "selected_interface": selected_interface,
                "check_md5": check_md5,
                "md5_v4": md5_v4 if check_md5 else "",
                "md5_v6": md5_v6 if check_md5 else "",
                **peer_info
            }
            
            if show_circuito and circuito:
                result["circuito"] = circuito
            
            return result
        
        return None