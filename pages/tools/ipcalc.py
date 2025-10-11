import streamlit as st
import ipaddress

def render():
    """Renderiza a calculadora de IP"""
    st.title("🔢 Calculadora de IP")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ip_input = st.text_input(
            "Endereço IP com CIDR",
            placeholder="Ex: 192.168.1.0/24",
            help="Digite um endereço IP no formato CIDR"
        )
    
    if ip_input:
        try:
            network = ipaddress.ip_network(ip_input, strict=False)
            
            st.divider()
            st.subheader("📊 Informações da Rede")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Endereço de Rede", str(network.network_address))
                st.metric("Primeiro Host", str(list(network.hosts())[0]) if network.num_addresses > 2 else "N/A")
            
            with col2:
                st.metric("Broadcast", str(network.broadcast_address))
                st.metric("Último Host", str(list(network.hosts())[-1]) if network.num_addresses > 2 else "N/A")
            
            with col3:
                st.metric("Máscara de Rede", str(network.netmask))
                st.metric("Total de Hosts", network.num_addresses - 2 if network.num_addresses > 2 else 0)
            
        except ValueError as e:
            st.error(f"❌ Endereço IP inválido: {str(e)}")