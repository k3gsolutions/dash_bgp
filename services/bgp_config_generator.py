"""
Módulo de Geração de Configuração BGP
Integrado com a aplicação Streamlit dash_bgp
"""

import streamlit as st
import json
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class TipoCircuito(str, Enum):
    """Tipos de circuito disponíveis"""
    CLIENTE = "cliente"
    OPERADORA = "operadora"
    OPERADORA_COMM = "operadora_comm"
    IX = "ix"
    CDN = "cdn"


@dataclass
class BGPPeeringConfig:
    """Modelo para configuração de BGP Peering"""
    nome: str
    tipo_circuito: str
    asn_local: int
    asn_remoto: int
    ipv4_local: str
    ipv4_remoto: str
    ipv6_local: Optional[str] = None
    ipv6_remoto: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return asdict(self)

    def validate(self) -> tuple[bool, str]:
        """Valida os dados"""
        if not self.nome:
            return False, "Nome é obrigatório"
        
        if not self.nome.startswith(('AS', 'CL')):
            return False, "Nome deve começar com 'AS' (operadora) ou 'CL' (cliente)"
        
        if not self.tipo_circuito:
            return False, "Tipo de circuito é obrigatório"
        
        if not self.ipv4_local or not self.ipv4_remoto:
            return False, "IPv4 local e remoto são obrigatórios"
        
        if self.ipv6_local and not self.ipv6_remoto:
            return False, "Se informar IPv6 local, deve informar IPv6 remoto"
        
        return True, "Validação ok"


class BGPConfigGenerator:
    """Gerador de configurações BGP"""

    @staticmethod
    def extract_circuito_id(nome: str) -> str:
        """Extrai ID do circuito do nome"""
        return nome.split('-')[0]

    @classmethod
    def generate_config(cls, config: BGPPeeringConfig) -> str:
        """Gera configuração BGP em formato de texto"""
        
        circuito_id = cls.extract_circuito_id(config.nome)
        asn_local = config.asn_local
        asn_remoto = config.asn_remoto
        
        config_lines = []
        config_lines.append("# " + "="*70)
        config_lines.append(f"# CONFIGURAÇÃO BGP - {config.nome}")
        config_lines.append(f"# Tipo: {config.tipo_circuito.upper()}")
        config_lines.append(f"# Gerada em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        config_lines.append("# " + "="*70)
        config_lines.append("")
        
        # Seção de filtros de prefixos IPv4
        config_lines.append("# IPv4 PREFIX-LISTS")
        config_lines.append(f"ip ip-prefix {circuito_id}-PREFIX-PREFERENCE-IPV4 index 10 permit 0.0.0.0 0 less-equal 32")
        config_lines.append("")
        
        # Seção de filtros de prefixos IPv6
        if config.ipv6_local and config.ipv6_remoto:
            config_lines.append("# IPv6 PREFIX-LISTS")
            config_lines.append(f"ipv6 ip-prefix {circuito_id}-PREFIX-PREFERENCE-IPV6 index 10 permit ::/0 less-equal 128")
            config_lines.append("")
        
        # Seção de AS-PATH filters
        config_lines.append("# AS-PATH FILTERS")
        config_lines.append(f"as-path-filter {circuito_id}-AS-PREFERENCE index 10 permit ^{asn_remoto}$")
        config_lines.append(f"as-path-filter {circuito_id}-AS-BLOCKLIST index 10 deny ^$")
        config_lines.append("")
        
        # Seção de Route-Policies IPv4
        config_lines.append("# ROUTE-POLICIES IPv4")
        config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV4 permit node 10")
        config_lines.append(f" if-match ip-prefix {circuito_id}-PREFIX-PREFERENCE-IPV4")
        config_lines.append(f" apply local-preference 201")
        config_lines.append(f" apply community 64777:5{circuito_id[2:]}00 64777:20000 64777:20010")
        config_lines.append(f"#")
        config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV4 permit node 2000")
        config_lines.append(f" if-match as-path-filter {circuito_id}-AS-PREFERENCE")
        config_lines.append(f" apply local-preference 200")
        config_lines.append(f" apply community 64777:5{circuito_id[2:]}00")
        config_lines.append(f"#")
        config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV4 permit node 3000")
        config_lines.append(f" apply local-preference 100")
        config_lines.append(f"#")
        config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV4 deny node 9999")
        config_lines.append(f"#")
        config_lines.append(f"route-policy {circuito_id}-EXPORT deny node 9999")
        config_lines.append("")
        
        # Seção de Route-Policies IPv6
        if config.ipv6_local and config.ipv6_remoto:
            config_lines.append("# ROUTE-POLICIES IPv6")
            config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV6 permit node 10")
            config_lines.append(f" if-match ipv6 address prefix-list {circuito_id}-PREFIX-PREFERENCE-IPV6")
            config_lines.append(f" apply local-preference 201")
            config_lines.append(f" apply community 64777:5{circuito_id[2:]}00 64777:20000 64777:20010")
            config_lines.append(f"#")
            config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV6 permit node 2000")
            config_lines.append(f" if-match as-path-filter {circuito_id}-AS-PREFERENCE")
            config_lines.append(f" apply local-preference 200")
            config_lines.append(f"#")
            config_lines.append(f"route-policy {circuito_id}-IMPORT-IPV6 deny node 9999")
            config_lines.append("")
        
        # Seção de BGP Peering
        config_lines.append("# BGP PEERING CONFIGURATION")
        config_lines.append(f"bgp {asn_local}")
        config_lines.append(f" peer {config.ipv4_remoto} as-number {asn_remoto}")
        config_lines.append(f" peer {config.ipv4_remoto} connect-interface {config.ipv4_local}")
        config_lines.append(f" peer {config.ipv4_remoto} description {config.nome}")
        
        if config.ipv6_local and config.ipv6_remoto:
            config_lines.append(f" peer {config.ipv6_remoto} as-number {asn_remoto}")
            config_lines.append(f" peer {config.ipv6_remoto} connect-interface {config.ipv6_local}")
            config_lines.append(f" peer {config.ipv6_remoto} description {config.nome}")
        
        config_lines.append("")
        
        # IPv4 Family
        config_lines.append("ipv4-family unicast")
        config_lines.append(f" peer {config.ipv4_remoto} enable")
        config_lines.append(f" peer {config.ipv4_remoto} route-policy {circuito_id}-IMPORT-IPV4 import")
        config_lines.append(f" peer {config.ipv4_remoto} route-policy {circuito_id}-EXPORT export")
        config_lines.append("")
        
        # IPv6 Family
        if config.ipv6_local and config.ipv6_remoto:
            config_lines.append("ipv6-family unicast")
            config_lines.append(f" peer {config.ipv6_remoto} enable")
            config_lines.append(f" peer {config.ipv6_remoto} route-policy {circuito_id}-IMPORT-IPV6 import")
            config_lines.append(f" peer {config.ipv6_remoto} route-policy {circuito_id}-EXPORT export")
            config_lines.append("")
        
        config_lines.append("# " + "="*70)
        
        return "\n".join(config_lines)


def render_config_generator():
    """Renderiza a página de gerador de configuração BGP no Streamlit"""
    
    st.set_page_config(page_title="Gerador BGP", layout="wide")
    
    st.title("🔧 Gerador de Configuração BGP")
    st.markdown("---")
    
    # Dividir em colunas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Dados do Peering")
        
        # Informações básicas
        nome = st.text_input(
            "Nome do Vizinho",
            placeholder="Ex: AS262663-IMPACTUS ou CL-EMPRESA-XYZ",
            help="Comece com 'AS' (operadora) ou 'CL' (cliente)"
        )
        
        tipo_circuito = st.selectbox(
            "Tipo de Circuito",
            options=[t.value for t in TipoCircuito],
            help="Selecione o tipo de circuito"
        )
        
        st.markdown("**ASN (Autonomous System Numbers)**")
        col_asn1, col_asn2 = st.columns(2)
        with col_asn1:
            asn_local = st.number_input("ASN Local", min_value=1, max_value=4200000000, value=64777)
        with col_asn2:
            asn_remoto = st.number_input("ASN Remoto", min_value=1, max_value=4200000000, value=262663)
        
        st.markdown("**IPv4**")
        col_ipv4_1, col_ipv4_2 = st.columns(2)
        with col_ipv4_1:
            ipv4_local = st.text_input("IPv4 Local", placeholder="Ex: 10.0.0.1")
        with col_ipv4_2:
            ipv4_remoto = st.text_input("IPv4 Remoto", placeholder="Ex: 10.0.0.2")
        
        st.markdown("**IPv6 (Opcional)**")
        col_ipv6_1, col_ipv6_2 = st.columns(2)
        with col_ipv6_1:
            ipv6_local = st.text_input("IPv6 Local", placeholder="Ex: 2001:db8::1", value="")
        with col_ipv6_2:
            ipv6_remoto = st.text_input("IPv6 Remoto", placeholder="Ex: 2001:db8::2", value="")
    
    with col2:
        st.subheader("📝 Preview & Ações")
        
        # Criar objeto de configuração
        config = BGPPeeringConfig(
            nome=nome,
            tipo_circuito=tipo_circuito,
            asn_local=int(asn_local),
            asn_remoto=int(asn_remoto),
            ipv4_local=ipv4_local,
            ipv4_remoto=ipv4_remoto,
            ipv6_local=ipv6_local if ipv6_local else None,
            ipv6_remoto=ipv6_remoto if ipv6_remoto else None,
        )
        
        # Validar
        is_valid, message = config.validate()
        
        if not is_valid:
            st.error(f"❌ {message}")
        else:
            st.success("✅ Dados validados com sucesso!")
            
            # Gerar configuração
            if st.button("🚀 Gerar Configuração", use_container_width=True, type="primary"):
                config_text = BGPConfigGenerator.generate_config(config)
                st.session_state.config_generated = config_text
                st.session_state.config_data = config.to_dict()
                st.session_state.generated_at = datetime.now()
    
    st.markdown("---")
    
    # Mostrar configuração gerada
    if "config_generated" in st.session_state:
        st.subheader("📄 Configuração Gerada")
        
        # Tabs para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["Arquivo TXT", "JSON", "Copiar"])
        
        with tab1:
            st.code(st.session_state.config_generated, language="text")
            st.download_button(
                label="📥 Baixar TXT",
                data=st.session_state.config_generated,
                file_name=f"{st.session_state.config_data['nome']}_bgp_config.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with tab2:
            config_json = json.dumps(st.session_state.config_data, indent=2, ensure_ascii=False)
            st.code(config_json, language="json")
            st.download_button(
                label="📥 Baixar JSON",
                data=config_json,
                file_name=f"{st.session_state.config_data['nome']}_bgp_config.json",
                mime="application/json",
                use_container_width=True
            )
        
        with tab3:
            st.text_area(
                "Copie a configuração:",
                value=st.session_state.config_generated,
                height=400,
                disabled=True
            )
        
        # Informações adicionais
        st.markdown("---")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Nome do Circuito", st.session_state.config_data['nome'])
        with col_info2:
            st.metric("Tipo", st.session_state.config_data['tipo_circuito'])
        with col_info3:
            st.metric("Gerada em", st.session_state.generated_at.strftime("%H:%M:%S"))


if __name__ == "__main__":
    render_config_generator()