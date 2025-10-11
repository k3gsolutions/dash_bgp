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

    def _parse_prefixes(self, text: str, version: str) -> Tuple[List[str], List[str]]:
        """Parse de prefixos IPv4 ou IPv6"""
        valid_prefixes = []
        invalid_prefixes = []
        
        if version == "ipv4":
            # Padrão mais simples para capturar prefixo completo IPv4/CIDR
            pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,3}\b'
            matches = re.findall(pattern, text)
            
            for match in matches:
                try:
                    prefix = match
                    ipaddress.IPv4Network(prefix, strict=False)
                    valid_prefixes.append(prefix)
                except (ipaddress.AddressValueError, ValueError):
                    invalid_prefixes.append(match)
        else:
            # Para IPv6, usar uma abordagem mais simples
            # Buscar por qualquer string que contenha ':' e '/' que possa ser um prefixo IPv6
            # Dividir o texto em palavras e testar cada uma
            words = re.findall(r'\S+', text)
            
            for word in words:
                if ':' in word and '/' in word:
                    try:
                        prefix = word
                        ipaddress.IPv6Network(prefix, strict=False)
                        valid_prefixes.append(prefix)
                    except (ipaddress.AddressValueError, ValueError):
                        invalid_prefixes.append(word)
        
        return valid_prefixes, invalid_prefixes

    def _lookup_asn(self, asn: str) -> str:
        """Busca informações do ASN"""
        try:
            if asn.startswith("AS"):
                asn_num = asn[2:]
            else:
                asn_num = asn
            
            url = f"https://stat.ripe.net/data/as-overview/data.json?resource={asn_num}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("holder", "")
        except:
            pass
        return ""

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
        """Formulário para configurações BGP"""
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
            help="Nome deve começar com CL- ou AS"
        )
        
        if not self._validate_customer_name(customer_name):
            st.warning("⚠️ Nome do cliente deve começar com 'CL-' ou 'AS'")
            return None
        
        # ASN Configuration
        st.markdown("### 🌐 Configuração de ASN")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            asn_local = st.text_input(
                "ASN Local *",
                placeholder="AS64512",
                help="ASN do seu roteador"
            )
        
        with col2:
            asn_remoto = st.text_input(
                "ASN Remoto *", 
                placeholder="AS64513",
                help="ASN do peer remoto"
            )
        
        # Lookup ASN
        asn_name = ""
        if asn_remoto and st.button("🔍 Buscar informações do ASN"):
            with st.spinner("Buscando informações..."):
                asn_name = self._lookup_asn(asn_remoto)
                st.session_state['asn_name'] = asn_name
                if asn_name:
                    st.success(f"ASN encontrado: **{asn_name}**")
                else:
                    st.warning("Não foi possível obter informações do ASN")
        
        # Exibir ASN salvo na sessão
        if 'asn_name' in st.session_state and st.session_state['asn_name']:
            st.info(f"**ASN Remoto:** {st.session_state['asn_name']}")
        
        # Prefixos IPv4
        st.markdown("### 📡 Configuração de Prefixos IPv4")
        ipv4_prefixes_text = st.text_area(
            "Prefixos IPv4",
            placeholder="192.168.1.0/24\n10.0.0.0/16\n172.16.0.0/12",
            height=100,
            help="Digite os prefixos IPv4, um por linha"
        )
        
        if st.button("✅ Validar Prefixos IPv4"):
            if ipv4_prefixes_text.strip():
                valid_prefixes, invalid_prefixes = self._parse_prefixes(ipv4_prefixes_text, "ipv4")
                
                if valid_prefixes:
                    st.session_state['ipv4_prefixes_data'] = valid_prefixes
                    st.success(f"✅ {len(valid_prefixes)} prefixos IPv4 válidos encontrados")
                    
                    # Exibir prefixos válidos
                    for prefix in valid_prefixes:
                        st.code(prefix)
                
                if invalid_prefixes:
                    st.error(f"❌ {len(invalid_prefixes)} prefixos inválidos encontrados")
                    for invalid in invalid_prefixes:
                        st.code(invalid)
            else:
                st.warning("Por favor, insira pelo menos um prefixo IPv4")
        
        # Exibir prefixos salvos
        if st.session_state.get('ipv4_prefixes_data'):
            st.info(f"**Prefixos IPv4 salvos:** {len(st.session_state['ipv4_prefixes_data'])}")
            with st.expander("Ver prefixos salvos"):
                for prefix in st.session_state['ipv4_prefixes_data']:
                    st.code(prefix)
        
        # Prefixos IPv6
        st.markdown("### 🌐 Configuração de Prefixos IPv6")
        ipv6_prefixes_text = st.text_area(
            "Prefixos IPv6",
            placeholder="2001:db8::/32\n2001:db8:1::/48",
            height=80,
            help="Digite os prefixos IPv6, um por linha"
        )
        
        if st.button("✅ Validar Prefixos IPv6"):
            if ipv6_prefixes_text.strip():
                valid_prefixes, invalid_prefixes = self._parse_prefixes(ipv6_prefixes_text, "ipv6")
                
                if valid_prefixes:
                    st.session_state['ipv6_prefixes_data'] = valid_prefixes
                    st.success(f"✅ {len(valid_prefixes)} prefixos IPv6 válidos encontrados")
                    
                    for prefix in valid_prefixes:
                        st.code(prefix)
                
                if invalid_prefixes:
                    st.error(f"❌ {len(invalid_prefixes)} prefixos inválidos encontrados")
                    for invalid in invalid_prefixes:
                        st.code(invalid)
            else:
                st.warning("Por favor, insira pelo menos um prefixo IPv6")
        
        # Exibir prefixos salvos
        if st.session_state.get('ipv6_prefixes_data'):
            st.info(f"**Prefixos IPv6 salvos:** {len(st.session_state['ipv6_prefixes_data'])}")
            with st.expander("Ver prefixos salvos"):
                for prefix in st.session_state['ipv6_prefixes_data']:
                    st.code(prefix)
        
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
        check_md5 = st.checkbox("Habilitar autenticação MD5", value=False)
        
        md5_v4 = ""
        md5_v6 = ""
        
        if check_md5:
            col1, col2 = st.columns(2)
            with col1:
                md5_v4 = st.text_input(
                    "Senha MD5 IPv4",
                    type="password",
                    help="Senha MD5 para sessão BGP IPv4"
                )
            with col2:
                md5_v6 = st.text_input(
                    "Senha MD5 IPv6", 
                    type="password",
                    help="Senha MD5 para sessão BGP IPv6"
                )
        
        # Circuito (opcional)
        show_circuito = st.checkbox("Adicionar informações de circuito", value=False)
        circuito = None
        if show_circuito:
            circuito = st.text_input(
                "Circuito/Tag",
                placeholder="Ex: CIRCUITO-12345",
                help="Informação adicional sobre o circuito"
            )
        
        # Validação final e botão
        can_generate = (
            customer_name and 
            asn_local and 
            asn_remoto and 
            (st.session_state.get('ipv4_prefixes_data') or st.session_state.get('ipv6_prefixes_data')) and
            peer_info
        )
        
        if not can_generate:
            st.warning("⚠️ Preencha todos os campos obrigatórios e valide os prefixos")
        
        # Botão para gerar configuração
        if st.button("🎯 Gerar Configuração BGP", type="primary", disabled=not can_generate):
            result = {
                "service_type": service_type,
                "customer_name": customer_name,
                "asn_local": asn_local,
                "asn_remoto": asn_remoto,
                "asn_name": st.session_state.get('asn_name', ''),
                "ipv4_prefixes": st.session_state.get('ipv4_prefixes_data', []),
                "ipv6_prefixes": st.session_state.get('ipv6_prefixes_data', []),
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