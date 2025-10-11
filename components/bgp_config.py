"""
Componente especializado para configurações BGP
"""
import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
import requests
import re
import ipaddress
from services.netbox_service import NetboxService

class BGPConfigComponent:
    """Componente para gerenciar configurações BGP"""
    
    def __init__(self):
        self.netbox = NetboxService()
    
    def render_asn_section(self, service_type: str) -> Tuple[str, str, str]:
        """
        Renderiza seção de configuração de ASN
        
        Args:
            service_type: Tipo de serviço BGP
            
        Returns:
            Tupla com (asn_local, asn_remoto, asn_name)
        """
        st.markdown("### 🌐 Configuração de ASN")
        
        col1, col2 = st.columns(2)
        
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
        
        # Lookup ASN
        asn_name = ""
        if asn_remoto and st.button("🔍 Buscar informações do ASN", key=f"lookup_asn_{service_type}"):
            with st.spinner("Buscando informações do ASN..."):
                asn_name = self._lookup_asn_info(asn_remoto)
                if asn_name:
                    st.session_state[f'asn_name_{service_type}'] = asn_name
                    st.success(f"**ASN encontrado:** {asn_name}")
                else:
                    st.warning("Não foi possível obter informações do ASN")
        
        # Exibir ASN salvo na sessão
        saved_asn_name = st.session_state.get(f'asn_name_{service_type}', '')
        if saved_asn_name:
            st.info(f"**ASN Remoto:** {saved_asn_name}")
        
        return asn_local, asn_remoto, saved_asn_name
    
    def render_prefixes_section(self, service_type: str) -> Tuple[List[str], List[str]]:
        """
        Renderiza seção de configuração de prefixos
        
        Args:
            service_type: Tipo de serviço BGP
            
        Returns:
            Tupla com (ipv4_prefixes, ipv6_prefixes)
        """
        # Inicializar session state
        ipv4_key = f'ipv4_prefixes_{service_type}'
        ipv6_key = f'ipv6_prefixes_{service_type}'
        
        if ipv4_key not in st.session_state:
            st.session_state[ipv4_key] = []
        if ipv6_key not in st.session_state:
            st.session_state[ipv6_key] = []
        
        # IPv4 Section
        st.markdown("### 📡 Prefixos IPv4")
        ipv4_text = st.text_area(
            "Prefixos IPv4",
            placeholder="192.168.1.0/24\n10.0.0.0/16\n172.16.0.0/12",
            height=100,
            help="Digite os prefixos IPv4, um por linha",
            key=f"ipv4_text_{service_type}"
        )
        
        if st.button("✅ Validar Prefixos IPv4", key=f"validate_ipv4_{service_type}"):
            if ipv4_text.strip():
                valid_prefixes, invalid_prefixes = self._parse_ipv4_prefixes(ipv4_text)
                
                if valid_prefixes:
                    st.session_state[ipv4_key] = valid_prefixes
                    st.success(f"✅ {len(valid_prefixes)} prefixos IPv4 válidos encontrados")
                    
                    with st.expander("Ver prefixos válidos"):
                        for prefix in valid_prefixes:
                            st.code(prefix)
                
                if invalid_prefixes:
                    st.error(f"❌ {len(invalid_prefixes)} prefixos inválidos encontrados")
                    with st.expander("Ver prefixos inválidos"):
                        for invalid in invalid_prefixes:
                            st.code(invalid)
            else:
                st.warning("Por favor, insira pelo menos um prefixo IPv4")
        
        # Exibir prefixos IPv4 salvos
        if st.session_state[ipv4_key]:
            st.info(f"**Prefixos IPv4 salvos:** {len(st.session_state[ipv4_key])}")
            with st.expander("Ver prefixos IPv4 salvos"):
                for prefix in st.session_state[ipv4_key]:
                    st.code(prefix)
        
        # IPv6 Section
        st.markdown("### 🌐 Prefixos IPv6")
        ipv6_text = st.text_area(
            "Prefixos IPv6",
            placeholder="2001:db8::/32\n2001:db8:1::/48",
            height=80,
            help="Digite os prefixos IPv6, um por linha",
            key=f"ipv6_text_{service_type}"
        )
        
        if st.button("✅ Validar Prefixos IPv6", key=f"validate_ipv6_{service_type}"):
            if ipv6_text.strip():
                valid_prefixes, invalid_prefixes = self._parse_ipv6_prefixes(ipv6_text)
                
                if valid_prefixes:
                    st.session_state[ipv6_key] = valid_prefixes
                    st.success(f"✅ {len(valid_prefixes)} prefixos IPv6 válidos encontrados")
                    
                    with st.expander("Ver prefixos válidos"):
                        for prefix in valid_prefixes:
                            st.code(prefix)
                
                if invalid_prefixes:
                    st.error(f"❌ {len(invalid_prefixes)} prefixos inválidos encontrados")
                    with st.expander("Ver prefixos inválidos"):
                        for invalid in invalid_prefixes:
                            st.code(invalid)
            else:
                st.warning("Por favor, insira pelo menos um prefixo IPv6")
        
        # Exibir prefixos IPv6 salvos
        if st.session_state[ipv6_key]:
            st.info(f"**Prefixos IPv6 salvos:** {len(st.session_state[ipv6_key])}")
            with st.expander("Ver prefixos IPv6 salvos"):
                for prefix in st.session_state[ipv6_key]:
                    st.code(prefix)
        
        return st.session_state[ipv4_key], st.session_state[ipv6_key]
    
    def render_peer_section(self, service_type: str) -> Dict[str, str]:
        """
        Renderiza seção de informações do peer
        
        Args:
            service_type: Tipo de serviço BGP
            
        Returns:
            Dict com informações do peer
        """
        st.markdown("### 🔗 Informações do Peer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            peer_ip_v4 = st.text_input(
                "Peer IPv4",
                placeholder="192.168.1.1",
                help="Endereço IPv4 do peer BGP",
                key=f"peer_ipv4_{service_type}"
            )
            
            local_ip_v4 = st.text_input(
                "Local IPv4",
                placeholder="192.168.1.2", 
                help="Seu endereço IPv4 local",
                key=f"local_ipv4_{service_type}"
            )
        
        with col2:
            peer_ip_v6 = st.text_input(
                "Peer IPv6",
                placeholder="2001:db8::1",
                help="Endereço IPv6 do peer BGP",
                key=f"peer_ipv6_{service_type}"
            )
            
            local_ip_v6 = st.text_input(
                "Local IPv6",
                placeholder="2001:db8::2",
                help="Seu endereço IPv6 local",
                key=f"local_ipv6_{service_type}"
            )
        
        # Validações básicas
        peer_info = {
            "peer_ip_v4": peer_ip_v4,
            "peer_ip_v6": peer_ip_v6,
            "local_ip_v4": local_ip_v4,
            "local_ip_v6": local_ip_v6
        }
        
        # Validar IPs se preenchidos
        validation_errors = []
        
        if peer_ip_v4 and not self._validate_ipv4(peer_ip_v4):
            validation_errors.append("Peer IPv4 inválido")
        
        if peer_ip_v6 and not self._validate_ipv6(peer_ip_v6):
            validation_errors.append("Peer IPv6 inválido")
            
        if local_ip_v4 and not self._validate_ipv4(local_ip_v4):
            validation_errors.append("Local IPv4 inválido")
            
        if local_ip_v6 and not self._validate_ipv6(local_ip_v6):
            validation_errors.append("Local IPv6 inválido")
        
        if validation_errors:
            for error in validation_errors:
                st.error(f"❌ {error}")
        
        return peer_info
    
    def render_md5_section(self, service_type: str) -> Tuple[bool, str, str]:
        """
        Renderiza seção de autenticação MD5
        
        Args:
            service_type: Tipo de serviço BGP
            
        Returns:
            Tupla com (enabled, md5_v4, md5_v6)
        """
        st.markdown("### 🔐 Autenticação MD5")
        
        check_md5 = st.checkbox(
            "Habilitar autenticação MD5",
            value=False,
            help="Usar senhas MD5 para autenticação BGP",
            key=f"md5_enabled_{service_type}"
        )
        
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
        
        return check_md5, md5_v4, md5_v6
    
    def render_communities_section(self, service_type: str) -> List[str]:
        """
        Renderiza seção de communities BGP (para serviços que usam)
        
        Args:
            service_type: Tipo de serviço BGP
            
        Returns:
            Lista de communities
        """
        if service_type not in ['upstream_comm', 'cdn_comm', 'ixbr_comm']:
            return []
        
        st.markdown("### 🏷️ BGP Communities")
        
        # Communities predefinidas baseadas no tipo
        predefined_communities = self._get_predefined_communities(service_type)
        
        if predefined_communities:
            st.info("**Communities sugeridas para este tipo de serviço:**")
            for community, description in predefined_communities.items():
                st.code(f"{community} - {description}")
        
        communities_text = st.text_area(
            "Communities BGP",
            placeholder="64512:100\n64512:200\n64512:300",
            height=100,
            help="Digite as communities BGP, uma por linha (formato: ASN:VALUE)",
            key=f"communities_{service_type}"
        )
        
        communities = []
        if communities_text.strip():
            communities = [c.strip() for c in communities_text.split('\n') if c.strip()]
            
            # Validar formato das communities
            invalid_communities = []
            valid_communities = []
            
            for community in communities:
                if self._validate_community_format(community):
                    valid_communities.append(community)
                else:
                    invalid_communities.append(community)
            
            if invalid_communities:
                st.error("❌ Communities com formato inválido:")
                for invalid in invalid_communities:
                    st.code(invalid)
                st.info("Formato correto: ASN:VALUE (ex: 64512:100)")
            
            communities = valid_communities
        
        return communities
    
    def _lookup_asn_info(self, asn: str) -> str:
        """Busca informações do ASN via API RIPE"""
        try:
            asn_num = asn.replace("AS", "").strip()
            url = f"https://stat.ripe.net/data/as-overview/data.json?resource={asn_num}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("holder", "")
            
        except Exception:
            pass
        
        return ""
    
    def _parse_ipv4_prefixes(self, text: str) -> Tuple[List[str], List[str]]:
        """Parse e validação de prefixos IPv4"""
        pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[1-2]?[0-9])\b'
        matches = re.findall(pattern, text)
        
        valid = []
        invalid = []
        
        for match in matches:
            try:
                ipaddress.IPv4Network(match, strict=False)
                valid.append(match)
            except:
                invalid.append(match)
        
        return valid, invalid
    
    def _parse_ipv6_prefixes(self, text: str) -> Tuple[List[str], List[str]]:
        """Parse e validação de prefixos IPv6"""
        # Pattern simplificado para IPv6/CIDR
        pattern = r'\b(?:[0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{0,4}\/(?:12[0-8]|1[0-1][0-9]|[1-9]?[0-9])\b'
        matches = re.findall(pattern, text)
        
        valid = []
        invalid = []
        
        for match in matches:
            try:
                ipaddress.IPv6Network(match, strict=False)
                valid.append(match)
            except:
                invalid.append(match)
        
        return valid, invalid
    
    def _validate_ipv4(self, ip: str) -> bool:
        """Valida endereço IPv4"""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except:
            return False
    
    def _validate_ipv6(self, ip: str) -> bool:
        """Valida endereço IPv6"""
        try:
            ipaddress.IPv6Address(ip)
            return True
        except:
            return False
    
    def _validate_community_format(self, community: str) -> bool:
        """Valida formato de community BGP (ASN:VALUE)"""
        pattern = r'^\d+:\d+$'
        return bool(re.match(pattern, community))
    
    def _get_predefined_communities(self, service_type: str) -> Dict[str, str]:
        """Retorna communities predefinidas por tipo de serviço"""
        communities_map = {
            'upstream_comm': {
                '64512:100': 'No Export to Customers',
                '64512:200': 'Export to Peers Only',
                '64512:300': 'Local Preference 300'
            },
            'cdn_comm': {
                '64512:410': 'CDN Content',
                '64512:420': 'CDN Cache', 
                '64512:430': 'CDN Edge'
            },
            'ixbr_comm': {
                '64512:1000': 'IX.br São Paulo',
                '64512:2000': 'IX.br Rio de Janeiro',
                '64512:3000': 'IX.br Fortaleza'
            }
        }
        
        return communities_map.get(service_type, {})