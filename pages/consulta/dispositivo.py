import streamlit as st
from services.netbox_service import NetboxService

def render():
    """Renderiza a página de consulta de dispositivo"""
    st.title("💻 Consulta de Dispositivo")
    
    service = NetboxService()
    
    # Buscar dispositivos
    with st.spinner("Carregando dispositivos..."):
        devices = service.get_devices()
    
    if not devices:
        st.warning("Nenhum dispositivo encontrado no sistema")
        return
    
    # Busca
    search = st.text_input("🔍 Buscar dispositivo", placeholder="Digite o nome do dispositivo...")
    
    # Filtrar dispositivos
    filtered_devices = devices
    if search:
        filtered_devices = [d for d in devices if search.lower() in d.get('name', '').lower()]
    
    st.write(f"**{len(filtered_devices)}** dispositivo(s) encontrado(s)")
    
    # Listar dispositivos
    for device in filtered_devices[:10]:  # Limitar a 10 para performance
        with st.expander(f"🖥️ {device.get('name')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {device.get('id')}")
                st.write(f"**Site:** {device.get('site', {}).get('name', 'N/A')}")
                st.write(f"**Tipo:** {device.get('device_type', {}).get('display', 'N/A')}")
            
            with col2:
                st.write(f"**Status:** {device.get('status', {}).get('label', 'N/A')}")
                st.write(f"**Serial:** {device.get('serial', 'N/A')}")
                st.write(f"**IP Primário:** {device.get('primary_ip', {}).get('address', 'N/A') if device.get('primary_ip') else 'N/A'}")