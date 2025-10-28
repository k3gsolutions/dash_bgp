"""
Página de análise de configurações de dispositivos
"""
# topo do arquivo (imports)
import streamlit as st
import pandas as pd
import re
import ipaddress
from typing import Dict, List, Optional, Tuple, Any
import json

class ConfigAnalyzer:
    """Analisador de configurações de dispositivos de rede"""
    
    def __init__(self):
        self.config_lines = []
        self.vendor = None
    
    def detect_vendor(self, config_text: str) -> str:
        """Detecta o vendor baseado no conteúdo da configuração"""
        config_lower = config_text.lower()
        
        # Patterns específicos por vendor
        if any(pattern in config_lower for pattern in ['vrp version', 'huawei versatile routing platform', 'display version', 'Software Version V200R']):
            return 'huawei'
        elif any(pattern in config_lower for pattern in ['cisco ios', 'cisco nexus', 'version 15.', 'version 16.']):
            return 'cisco'
        elif any(pattern in config_lower for pattern in ['routeros', 'mikrotik', '/interface', '/ip address']):
            return 'mikrotik'
        else:
            return 'unknown'
    
    def parse_config(self, config_text: str):
        """Parse inicial da configuração"""
        self.config_lines = config_text.splitlines()
        self.vendor = self.detect_vendor(config_text)
        return self.vendor
    
    # ===========================================
    # ANÁLISE DE INTERFACES E IPs
    # ===========================================
    
    def analyze_interfaces_cisco(self) -> List[Dict[str, Any]]:
        """Analisa interfaces em configurações Cisco"""
        interfaces = []
        current_interface = None
        interface_data = {}
        
        for line in self.config_lines:
            line = line.strip()
            
            # Interface declaration
            if line.startswith('interface '):
                if current_interface:
                    interfaces.append(interface_data)
                
                current_interface = line.replace('interface ', '')
                interface_data = {
                    'name': current_interface,
                    'ip_address': None,
                    'subnet_mask': None,
                    'description': None,
                    'status': 'unknown',
                    'vlan': None,
                    'type': self._get_interface_type(current_interface)
                }
            
            elif current_interface:
                # IP address
                if line.startswith('ip address '):
                    parts = line.split()
                    if len(parts) >= 3:
                        interface_data['ip_address'] = parts[2]
                        if len(parts) >= 4:
                            interface_data['subnet_mask'] = parts[3]
                
                # Description
                elif line.startswith('description '):
                    interface_data['description'] = line.replace('description ', '')
                
                # Status
                elif line == 'shutdown':
                    interface_data['status'] = 'shutdown'
                elif line == 'no shutdown':
                    interface_data['status'] = 'up'
                
                # VLAN
                elif line.startswith('switchport access vlan '):
                    interface_data['vlan'] = line.split()[-1]
        
        # Adicionar última interface
        if current_interface and interface_data:
            interfaces.append(interface_data)
        
        return interfaces
    
    def analyze_interfaces_huawei(self) -> List[Dict[str, Any]]:
        """Analisa interfaces em configurações Huawei"""
        interfaces = []
        current_interface = None
        interface_data = {}
        
        for line in self.config_lines:
            line = line.strip()
            
            # Interface declaration
            if line.startswith('interface '):
                if current_interface:
                    interfaces.append(interface_data)
                
                current_interface = line.replace('interface ', '')
                interface_data = {
                    'name': current_interface,
                    'ip_address': None,
                    'subnet_mask': None,
                    'description': None,
                    'status': 'unknown',
                    'vlan': None,
                    'type': self._get_interface_type(current_interface)
                }
            
            elif current_interface:
                # IP address
                if line.startswith('ip address '):
                    parts = line.split()
                    if len(parts) >= 3:
                        interface_data['ip_address'] = parts[2]
                        if len(parts) >= 4:
                            interface_data['subnet_mask'] = parts[3]
                
                # Description
                elif line.startswith('description '):
                    interface_data['description'] = line.replace('description ', '')
                
                # Status
                elif line == 'shutdown':
                    interface_data['status'] = 'shutdown'
                elif line == 'undo shutdown':
                    interface_data['status'] = 'up'
                
                # VLAN
                elif 'vlan' in line.lower():
                    vlan_match = re.search(r'vlan\s+(\d+)', line.lower())
                    if vlan_match:
                        interface_data['vlan'] = vlan_match.group(1)
        
        # Adicionar última interface
        if current_interface and interface_data:
            interfaces.append(interface_data)
        
        return interfaces
    
    def analyze_interfaces_mikrotik(self) -> List[Dict[str, Any]]:
        """Analisa interfaces em configurações MikroTik"""
        interfaces = []
        
        # Pattern para IP addresses do MikroTik
        ip_pattern = r'/ip address\s+add address=([0-9./]+)\s+interface=([^\s]+)'
        
        for line in self.config_lines:
            match = re.search(ip_pattern, line)
            if match:
                ip_cidr = match.group(1)
                interface_name = match.group(2)
                
                # Parse IP/CIDR
                try:
                    network = ipaddress.IPv4Network(ip_cidr, strict=False)
                    ip_address = str(network.network_address)
                    subnet_mask = str(network.netmask)
                except:
                    ip_address = ip_cidr.split('/')[0] if '/' in ip_cidr else ip_cidr
                    subnet_mask = None
                
                interfaces.append({
                    'name': interface_name,
                    'ip_address': ip_address,
                    'subnet_mask': subnet_mask,
                    'description': None,
                    'status': 'up',
                    'vlan': None,
                    'type': self._get_interface_type(interface_name)
                })
        
        return interfaces
    
    def _get_interface_type(self, interface_name: str) -> str:
        """Determina o tipo da interface baseado no nome"""
        name_lower = interface_name.lower()
        
        if any(x in name_lower for x in ['gigabit', 'gig', 'ge-', 'ge']):
            return 'gigabit'
        elif any(x in name_lower for x in ['fastethernet', 'fast', 'fe-', 'fa']):
            return 'fastethernet'
        elif any(x in name_lower for x in ['10gig', 'tengig', 'xe-', 'te']):
            return '10gigabit'
        elif any(x in name_lower for x in ['loopback', 'lo']):
            return 'loopback'
        elif any(x in name_lower for x in ['vlan', 'vlanif']):
            return 'vlan'
        elif any(x in name_lower for x in ['tunnel', 'tun']):
            return 'tunnel'
        else:
            return 'other'
    
    # ===========================================
    # ANÁLISE BGP
    # ===========================================
    
    def analyze_bgp_cisco(self) -> Dict[str, Any]:
        """Analisa configuração BGP Cisco"""
        bgp_data = {
            'local_as': None,
            'router_id': None,
            'neighbors': [],
            'networks': [],
            'vrfs': []
        }
        
        current_vrf = None
        in_bgp_config = False
        
        for line in self.config_lines:
            line = line.strip()
            
            # BGP process
            if line.startswith('router bgp '):
                bgp_data['local_as'] = line.split()[-1]
                in_bgp_config = True
            
            elif in_bgp_config:
                # Router ID
                if line.startswith('bgp router-id '):
                    bgp_data['router_id'] = line.split()[-1]
                
                # VRF
                elif line.startswith('address-family ipv4 vrf '):
                    current_vrf = line.split()[-1]
                    if current_vrf not in bgp_data['vrfs']:
                        bgp_data['vrfs'].append(current_vrf)
                
                # Neighbors
                elif line.startswith('neighbor '):
                    parts = line.split()
                    if len(parts) >= 4:
                        neighbor_ip = parts[1]
                        
                        if 'remote-as' in line:
                            remote_as = parts[-1]
                            neighbor = {
                                'ip': neighbor_ip,
                                'remote_as': remote_as,
                                'vrf': current_vrf or 'default',
                                'description': None
                            }
                            
                            # Procurar description do neighbor
                            for desc_line in self.config_lines:
                                if f'neighbor {neighbor_ip} description' in desc_line:
                                    neighbor['description'] = desc_line.split('description ', 1)[1]
                                    break
                            
                            bgp_data['neighbors'].append(neighbor)
                
                # Networks
                elif line.startswith('network '):
                    network = line.split()[1]
                    bgp_data['networks'].append({
                        'network': network,
                        'vrf': current_vrf or 'default'
                    })
                
                # End of BGP config
                elif line == '!':
                    in_bgp_config = False
        
        return bgp_data
    
    def analyze_bgp_huawei(self) -> Dict[str, Any]:
        """Analisa configuração BGP Huawei"""
        bgp_data = {
            'local_as': None,
            'router_id': None,
            'neighbors': [],
            'networks': [],
            'vrfs': []
        }
        
        current_vrf = None
        in_bgp_config = False
        
        for line in self.config_lines:
            line = line.strip()
            
            # BGP process
            if line.startswith('bgp '):
                bgp_data['local_as'] = line.split()[1]
                in_bgp_config = True
            
            elif in_bgp_config:
                # Router ID
                if line.startswith('router-id '):
                    bgp_data['router_id'] = line.split()[-1]
                
                # VRF/VPN-instance
                elif 'ipv4-family vpn-instance' in line:
                    current_vrf = line.split()[-1]
                    if current_vrf not in bgp_data['vrfs']:
                        bgp_data['vrfs'].append(current_vrf)
                
                # Peers
                elif line.startswith('peer '):
                    parts = line.split()
                    if len(parts) >= 4 and 'as-number' in line:
                        peer_ip = parts[1]
                        remote_as = parts[-1]
                        
                        neighbor = {
                            'ip': peer_ip,
                            'remote_as': remote_as,
                            'vrf': current_vrf or 'default',
                            'description': None
                        }
                        
                        # Procurar description
                        for desc_line in self.config_lines:
                            if f'peer {peer_ip} description' in desc_line:
                                neighbor['description'] = desc_line.split('description ', 1)[1]
                                break
                        
                        bgp_data['neighbors'].append(neighbor)
                
                # Networks
                elif line.startswith('network '):
                    network = line.split()[1]
                    bgp_data['networks'].append({
                        'network': network,
                        'vrf': current_vrf or 'default'
                    })
        
        return bgp_data
    
    def analyze_bgp_mikrotik(self) -> Dict[str, Any]:
        """Analisa configuração BGP MikroTik"""
        bgp_data = {
            'local_as': None,
            'router_id': None,
            'neighbors': [],
            'networks': [],
            'vrfs': []
        }
        
        # BGP instance e router-id
        for line in self.config_lines:
            if '/routing bgp instance' in line and 'as=' in line:
                as_match = re.search(r'as=(\d+)', line)
                if as_match:
                    bgp_data['local_as'] = as_match.group(1)
            
            elif '/routing bgp instance' in line and 'router-id=' in line:
                rid_match = re.search(r'router-id=([0-9.]+)', line)
                if rid_match:
                    bgp_data['router_id'] = rid_match.group(1)
            
            # BGP peers
            elif '/routing bgp peer' in line:
                peer_match = re.search(r'remote-address=([0-9.]+)', line)
                as_match = re.search(r'remote-as=(\d+)', line)
                
                if peer_match and as_match:
                    neighbor = {
                        'ip': peer_match.group(1),
                        'remote_as': as_match.group(1),
                        'vrf': 'default',
                        'description': None
                    }
                    bgp_data['neighbors'].append(neighbor)
            
            # BGP networks
            elif '/routing bgp network' in line:
                net_match = re.search(r'network=([0-9./]+)', line)
                if net_match:
                    bgp_data['networks'].append({
                        'network': net_match.group(1),
                        'vrf': 'default'
                    })
        
        return bgp_data
    
    # ===========================================
    # ANÁLISE L2VPN
    # ===========================================
    
    def analyze_l2vpn_cisco(self) -> List[Dict[str, Any]]:
        """Analisa circuitos L2VPN Cisco"""
        l2vpn_circuits = []
        
        for line in self.config_lines:
            line = line.strip()
            
            # Xconnect
            if 'xconnect' in line.lower():
                parts = line.split()
                if len(parts) >= 3:
                    l2vpn_circuits.append({
                        'type': 'xconnect',
                        'peer': parts[1] if len(parts) > 1 else 'unknown',
                        'vc_id': parts[2] if len(parts) > 2 else 'unknown',
                        'encapsulation': 'mpls' if 'mpls' in line else 'unknown',
                        'interface': None
                    })
            
            # L2VPN bridge-domain
            elif line.startswith('bridge-domain '):
                bd_id = line.split()[1]
                l2vpn_circuits.append({
                    'type': 'bridge-domain',
                    'bd_id': bd_id,
                    'peer': None,
                    'vc_id': None,
                    'encapsulation': 'ethernet',
                    'interface': None
                })
        
        return l2vpn_circuits
    
    def analyze_l2vpn_huawei(self) -> List[Dict[str, Any]]:
        """Analisa circuitos L2VPN Huawei"""
        l2vpn_circuits = []
        
        current_vsi = None
        
        for line in self.config_lines:
            line = line.strip()
            
            # VSI (Virtual Switch Instance)
            if line.startswith('vsi '):
                current_vsi = line.split()[1]
            
            elif current_vsi and 'pwsignal ldp' in line:
                # PWE3 LDP signaling
                l2vpn_circuits.append({
                    'type': 'vsi',
                    'vsi_name': current_vsi,
                    'peer': None,
                    'vc_id': None,
                    'encapsulation': 'ethernet',
                    'signaling': 'ldp'
                })
            
            # L2VC (Layer 2 Virtual Circuit)
            elif 'l2vc' in line.lower():
                parts = line.split()
                l2vpn_circuits.append({
                    'type': 'l2vc',
                    'peer': parts[1] if len(parts) > 1 else 'unknown',
                    'vc_id': parts[2] if len(parts) > 2 else 'unknown',
                    'encapsulation': 'mpls',
                    'signaling': 'ldp'
                })
        
        return l2vpn_circuits
    
    def analyze_l2vpn_mikrotik(self) -> List[Dict[str, Any]]:
        """Analisa circuitos L2VPN MikroTik"""
        l2vpn_circuits = []
        
        for line in self.config_lines:
            # VPLS
            if '/interface vpls' in line:
                vpls_match = re.search(r'name=([^\s]+)', line)
                remote_match = re.search(r'remote-peer=([0-9.]+)', line)
                
                if vpls_match:
                    l2vpn_circuits.append({
                        'type': 'vpls',
                        'name': vpls_match.group(1),
                        'peer': remote_match.group(1) if remote_match else 'unknown',
                        'vc_id': None,
                        'encapsulation': 'mpls'
                    })
            
            # L2TP
            elif '/interface l2tp-client' in line or '/interface l2tp-server' in line:
                name_match = re.search(r'name=([^\s]+)', line)
                if name_match:
                    l2vpn_circuits.append({
                        'type': 'l2tp',
                        'name': name_match.group(1),
                        'peer': 'configured',
                        'vc_id': None,
                        'encapsulation': 'l2tp'
                    })
        
        return l2vpn_circuits
    
    # ===========================================
    # MÉTODOS PRINCIPAIS
    # ===========================================
    
    def analyze_interfaces(self) -> List[Dict[str, Any]]:
        """Método principal para análise de interfaces"""
        if self.vendor == 'cisco':
            return self.analyze_interfaces_cisco()
        elif self.vendor == 'huawei':
            return self.analyze_interfaces_huawei()
        elif self.vendor == 'mikrotik':
            return self.analyze_interfaces_mikrotik()
        else:
            return []
    
    def analyze_bgp(self) -> Dict[str, Any]:
        """Método principal para análise BGP"""
        if self.vendor == 'cisco':
            return self.analyze_bgp_cisco()
        elif self.vendor == 'huawei':
            return self.analyze_bgp_huawei()
        elif self.vendor == 'mikrotik':
            return self.analyze_bgp_mikrotik()
        else:
            return {}
    
    def analyze_l2vpn(self) -> List[Dict[str, Any]]:
        """Método principal para análise L2VPN"""
        if self.vendor == 'cisco':
            return self.analyze_l2vpn_cisco()
        elif self.vendor == 'huawei':
            return self.analyze_l2vpn_huawei()
        elif self.vendor == 'mikrotik':
            return self.analyze_l2vpn_mikrotik()
        else:
            return []


def render():
    """Renderiza a página de análise de configuração"""
    
    st.title("🔍 Analisador de Configurações de Dispositivos")
    st.markdown("---")
    
    # Upload de arquivo
    st.markdown("### 📁 Upload da Configuração")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo de configuração (running-config)",
        type=['txt', 'cfg', 'conf'],
        help="Aceita arquivos de configuração de dispositivos Cisco, Huawei e MikroTik"
    )
    
    if not uploaded_file:
        st.info("👆 Por favor, faça upload de um arquivo de configuração para continuar")
        return
    
    # Ler conteúdo do arquivo
    try:
        config_content = uploaded_file.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            config_content = uploaded_file.read().decode('latin-1')
        except:
            st.error("❌ Erro ao ler o arquivo. Verifique a codificação.")
            return
    
    # Inicializar analisador
    analyzer = ConfigAnalyzer()
    detected_vendor = analyzer.parse_config(config_content)
    
    # Exibir informações do arquivo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Arquivo", uploaded_file.name)
    with col2:
        st.metric("📏 Linhas", len(analyzer.config_lines))
    with col3:
        vendor_icon = {
            'cisco': '🔷',
            'huawei': '🔶', 
            'mikrotik': '🔴',
            'unknown': '❓'
        }
        st.metric("🏭 Vendor", f"{vendor_icon.get(detected_vendor, '❓')} {detected_vendor.title()}")
    
    if detected_vendor == 'unknown':
        st.warning("⚠️ Vendor não detectado automaticamente. Os resultados podem ser limitados.")
        
        # Seleção manual de vendor (um por vez)
        st.markdown("### 🏭 Seleção manual de Vendor")
        colv1, colv2, colv3 = st.columns(3)
        with colv1:
            v_cisco = st.checkbox("Cisco")
        with colv2:
            v_huawei = st.checkbox("Huawei")
        with colv3:
            v_mikrotik = st.checkbox("MikroTik")
        
        selected_count = sum([v_cisco, v_huawei, v_mikrotik])
        if selected_count > 1:
            st.warning("⚠️ Selecione apenas um vendor por vez")
            return
        elif selected_count == 1:
            manual_vendor = 'cisco' if v_cisco else ('huawei' if v_huawei else 'mikrotik')
            analyzer.vendor = manual_vendor
            detected_vendor = manual_vendor
            st.success(f"✅ Vendor definido manualmente: {manual_vendor.title()}")
        else:
            st.info("Selecione um vendor para continuar ou prossiga com detecção limitada.")
    
    st.markdown("---")
    
    # Seleção do tipo de análise
    st.markdown("### ⚙️ Selecione o Tipo de Análise")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analyze_interfaces = st.checkbox(
            "🌐 **Interfaces e IPs**",
            help="Lista todas as interfaces configuradas e seus endereços IP"
        )
    
    with col2:
        analyze_bgp = st.checkbox(
            "📡 **Configurações BGP**", 
            help="Extrai informações de peers BGP, ASNs e redes anunciadas"
        )
    
    with col3:
        analyze_l2vpn = st.checkbox(
            "🔗 **Circuitos L2VPN**",
            help="Identifica VSIs, L2VCs e outras configurações de L2VPN"
        )
    
    # Executar análises selecionadas
    if any([analyze_interfaces, analyze_bgp, analyze_l2vpn]):
        st.markdown("---")
        
        if analyze_interfaces:
            st.markdown("## 🌐 Análise de Interfaces")
            interfaces = analyzer.analyze_interfaces()
            
            if interfaces:
                st.success(f"✅ Encontradas **{len(interfaces)}** interfaces")
                
                # Criar DataFrame para exibição
                interface_data = []
                for iface in interfaces:
                    interface_data.append([
                        iface['name'],
                        iface['type'],
                        iface['ip_address'] or '-',
                        iface['subnet_mask'] or '-',
                        iface['status'] or '-',
                        iface['vlan'] or '-',
                        iface['description'] or '-'
                    ])
                
                # Após montar 'interface_data' (lista de listas) para Interfaces:
                df_interfaces = pd.DataFrame(
                    interface_data,
                    columns=['Interface', 'Tipo', 'IP Address', 'Subnet Mask', 'Status', 'VLAN', 'Descrição']
                )
                st.dataframe(df_interfaces, use_container_width=True)
                
                # Download CSV
                csv_data = "Interface,Tipo,IP Address,Subnet Mask,Status,VLAN,Descrição\n"
                for row in interface_data:
                    csv_data += ",".join(str(cell) for cell in row) + "\n"
                
                st.download_button(
                    label="📥 Download CSV - Interfaces",
                    data=csv_data,
                    file_name=f"interfaces_{uploaded_file.name}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Nenhuma interface encontrada")
        
        if analyze_bgp:
            st.markdown("## 📡 Análise de Configurações BGP")
            bgp_data = analyzer.analyze_bgp()
            
            if bgp_data and (bgp_data.get('neighbors') or bgp_data.get('local_as')):
                # Informações gerais BGP
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🏢 ASN Local", bgp_data.get('local_as', 'N/A'))
                with col2:
                    st.metric("🆔 Router ID", bgp_data.get('router_id', 'N/A'))
                with col3:
                    st.metric("👥 Neighbors", len(bgp_data.get('neighbors', [])))
                
                # Tabela de neighbors
                if bgp_data.get('neighbors'):
                    st.markdown("### 👥 BGP Neighbors")
                    neighbor_data = []
                    for neighbor in bgp_data['neighbors']:
                        neighbor_data.append([
                            neighbor['ip'],
                            neighbor['remote_as'],
                            neighbor['vrf'],
                            neighbor['description'] or '-'
                        ])
                    
                    # Após montar 'neighbor_data' (lista de listas) para BGP Neighbors:
                    df_neighbors = pd.DataFrame(
                        neighbor_data,
                        columns=['Peer IP', 'Remote AS', 'VRF', 'Descrição']
                    )
                    st.dataframe(df_neighbors, use_container_width=True)
                
                # Redes anunciadas
                if bgp_data.get('networks'):
                    st.markdown("### 📢 Redes Anunciadas")
                    network_data = []
                    for network in bgp_data['networks']:
                        network_data.append([
                            network['network'],
                            network['vrf']
                        ])
                    
                    df_networks = pd.DataFrame(
                        network_data,
                        columns=['Rede', 'VRF']
                    )
                    st.dataframe(df_networks, use_container_width=True)
                
                # VRFs
                if bgp_data.get('vrfs'):
                    st.markdown("### 🏷️ VRFs Configuradas")
                    for vrf in bgp_data['vrfs']:
                        st.code(vrf)
                
                # Download JSON
                json_data = json.dumps(bgp_data, indent=2)
                st.download_button(
                    label="📥 Download JSON - BGP Config",
                    data=json_data,
                    file_name=f"bgp_config_{uploaded_file.name}.json",
                    mime="application/json"
                )
            else:
                st.warning("⚠️ Nenhuma configuração BGP encontrada")
        
        if analyze_l2vpn:
            st.markdown("## 🔗 Análise de Circuitos L2VPN")
            l2vpn_circuits = analyzer.analyze_l2vpn()
            
            if l2vpn_circuits:
                st.success(f"✅ Encontrados **{len(l2vpn_circuits)}** circuitos L2VPN")
                
                # Tabela de circuitos
                circuit_data = []
                for circuit in l2vpn_circuits:
                    circuit_data.append([
                        circuit.get('type', 'unknown'),
                        circuit.get('name', circuit.get('vsi_name', 'N/A')),
                        circuit.get('peer', 'N/A'),
                        circuit.get('vc_id', 'N/A'),
                        circuit.get('encapsulation', 'N/A'),
                        circuit.get('signaling', 'N/A')
                    ])
                
                # Após montar 'circuit_data' (lista de listas) para L2VPN Circuits:
                df_circuits = pd.DataFrame(
                    circuit_data,
                    columns=['Tipo', 'Nome/VSI', 'Peer', 'VC ID', 'Encapsulation', 'Signaling']
                )
                st.dataframe(df_circuits, use_container_width=True)
                
                # Download CSV
                csv_data = "Tipo,Nome/VSI,Peer,VC ID,Encapsulation,Signaling\n"
                for row in circuit_data:
                    csv_data += ",".join(str(cell) for cell in row) + "\n"
                
                st.download_button(
                    label="📥 Download CSV - L2VPN Circuits",
                    data=csv_data,
                    file_name=f"l2vpn_circuits_{uploaded_file.name}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Nenhum circuito L2VPN encontrado")
    
    else:
        st.info("👆 Selecione pelo menos um tipo de análise acima")
    
    st.markdown("### 🔗 Circuitos / Contextos L2VPN")
    # Lógica unificada: sempre usa analyze_vlan_contexts()
    vlan_rows = analyzer.analyze_vlan_contexts()
    if vlan_rows:
        df_vlans = pd.DataFrame(
            vlan_rows,
            columns=['Vlan', 'Descrição', 'Acessos', 'IP', 'MASK4', 'IPv6', 'MASK6', 'L2VC', 'NEIGHBOR', 'VPLS-ID', 'MTU', 'RAW']
        )
        st.dataframe(df_vlans, use_container_width=True)
    
        # Download CSV unificado (inclui vendor no nome)
        vendor_name = analyzer.vendor or 'unknown'
        csv_header = 'Vlan,Descrição,Acessos,IP,MASK4,IPv6,MASK6,L2VC,NEIGHBOR,VPLS-ID,MTU,RAW\n'
        csv_data = csv_header + '\n'.join([
            ','.join([
                str(row.get('Vlan', '')),
                str(row.get('Descrição', '')) if row.get('Descrição') else '',
                str(row.get('Acessos', '')) if row.get('Acessos') else '',
                str(row.get('IP', '')) if row.get('IP') else '',
                str(row.get('MASK4', '')) if row.get('MASK4') else '',
                str(row.get('IPv6', '')) if row.get('IPv6') else '',
                str(row.get('MASK6', '')) if row.get('MASK6') else '',
                str(row.get('L2VC', 'não')),
                str(row.get('NEIGHBOR', '')) if row.get('NEIGHBOR') else '',
                str(row.get('VPLS-ID', '')) if row.get('VPLS-ID') is not None else '',
                str(row.get('MTU', 1500)),
                str(row.get('RAW', 'não'))
            ])
            for row in vlan_rows
        ])
        st.download_button(
            label="📥 Download CSV - VLAN Contextos",
            data=csv_data,
            file_name=f"vlan_contexts_{vendor_name}_{uploaded_file.name}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Nenhum contexto de VLAN/L2VPN encontrado")
    
    st.markdown("### 🔗 Circuitos / Contextos L2VPN")
    # Lógica unificada: sempre usa analyze_vlan_contexts()
    vlan_rows = analyzer.analyze_vlan_contexts()
    if vlan_rows:
        df_vlans = pd.DataFrame(
            vlan_rows,
            columns=['Vlan', 'Descrição', 'Acessos', 'IP', 'MASK4', 'IPv6', 'MASK6', 'L2VC', 'NEIGHBOR', 'VPLS-ID', 'MTU', 'RAW']
        )
        st.dataframe(df_vlans, use_container_width=True)
    
        # Download CSV unificado (inclui vendor no nome)
        vendor_name = analyzer.vendor or 'unknown'
        csv_header = 'Vlan,Descrição,Acessos,IP,MASK4,IPv6,MASK6,L2VC,NEIGHBOR,VPLS-ID,MTU,RAW\n'
        csv_data = csv_header + '\n'.join([
            ','.join([
                str(row.get('Vlan', '')),
                str(row.get('Descrição', '')) if row.get('Descrição') else '',
                str(row.get('Acessos', '')) if row.get('Acessos') else '',
                str(row.get('IP', '')) if row.get('IP') else '',
                str(row.get('MASK4', '')) if row.get('MASK4') else '',
                str(row.get('IPv6', '')) if row.get('IPv6') else '',
                str(row.get('MASK6', '')) if row.get('MASK6') else '',
                str(row.get('L2VC', 'não')),
                str(row.get('NEIGHBOR', '')) if row.get('NEIGHBOR') else '',
                str(row.get('VPLS-ID', '')) if row.get('VPLS-ID') is not None else '',
                str(row.get('MTU', 1500)),
                str(row.get('RAW', 'não'))
            ])
            for row in vlan_rows
        ])
        st.download_button(
            label="📥 Download CSV - VLAN Contextos",
            data=csv_data,
            file_name=f"vlan_contexts_{vendor_name}_{uploaded_file.name}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Nenhum contexto de VLAN/L2VPN encontrado")


def analyze_vlan_contexts_huawei(self) -> List[Dict[str, Any]]:
    vlan_descriptions: Dict[int, str] = {}
    vlan_accesses: Dict[int, set] = {}
    vlan_vlanif_info: Dict[int, Dict[str, Any]] = {}
    present_vlans: set = set()

    current_interface: Optional[str] = None
    in_vlan_block = False
    current_vlan_id: Optional[int] = None

    for raw_line in self.config_lines:
        line = raw_line.strip()

        if line.startswith('vlan '):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                current_vlan_id = int(parts[1])
                present_vlans.add(current_vlan_id)
                in_vlan_block = True
                continue

        if in_vlan_block:
            if line.lower().startswith('name '):
                desc = line.split('name ', 1)[1].strip()
                if current_vlan_id is not None:
                    vlan_descriptions[current_vlan_id] = desc
            if line == '!' or line.startswith('vlan '):
                in_vlan_block = False
                current_vlan_id = None

        if line.startswith('interface '):
            current_interface = line.split('interface ', 1)[1].strip()
            if current_interface.lower().startswith('vlan'):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    present_vlans.add(vid)
                    vlan_vlanif_info.setdefault(vid, {
                        'ip': None, 'mask4': None,
                        'ipv6': None, 'mask6': None,
                        'l2vc': False, 'neighbor': None,
                        'vpls_id': None, 'mtu': 1500, 'raw': False
                    })
                continue

        if current_interface:
            if 'switchport access vlan ' in line.lower():
                try:
                    vlan_id = int(line.split()[-1])
                    present_vlans.add(vlan_id)
                    vlan_accesses.setdefault(vlan_id, set()).add(current_interface)
                except ValueError:
                    pass

            if line.startswith('ip address '):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    parts = line.split()
                    if len(parts) >= 4:
                        info = vlan_vlanif_info.setdefault(vid, {
                            'ip': None, 'mask4': None,
                            'ipv6': None, 'mask6': None,
                            'l2vc': False, 'neighbor': None,
                            'vpls_id': None, 'mtu': 1500, 'raw': False
                        })
                        info['ip'] = parts[2]
                        info['mask4'] = parts[3]

            if line.lower().startswith('ipv6 address '):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    addr = line.split('ipv6 address ', 1)[1].strip()
                    if '/' in addr:
                        ip6, pfx = addr.split('/', 1)
                        info = vlan_vlanif_info.setdefault(vid, {
                            'ip': None, 'mask4': None,
                            'ipv6': None, 'mask6': None,
                            'l2vc': False, 'neighbor': None,
                            'vpls_id': None, 'mtu': 1500, 'raw': False
                        })
                        info['ipv6'] = ip6
                        info['mask6'] = pfx

        if 'xconnect' in line.lower():
            parts = line.split()
            neighbor = None
            vc_id = None
            mtu = None
            raw = (' raw' in line.lower()) or line.lower().endswith('raw')

            for i, t in enumerate(parts):
                if t.lower() == 'xconnect' and i + 1 < len(parts):
                    neighbor = parts[i + 1]
                    for j in range(i + 2, min(i + 6, len(parts))):
                        if parts[j].isdigit():
                            vc_id = int(parts[j])
                            break
                        for j in range(i + 2, len(parts)):
                            if parts[j].lower() == 'mtu' and j + 1 < len(parts) and parts[j + 1].isdigit():
                                mtu = int(parts[j + 1])
                                break
                            break

            if current_interface and current_interface.lower().startswith('vlan'):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    info = vlan_vlanif_info.setdefault(vid, {
                        'ip': None, 'mask4': None,
                        'ipv6': None, 'mask6': None,
                        'l2vc': False, 'neighbor': None,
                        'vpls_id': None, 'mtu': 1500, 'raw': False
                    })
                    info['l2vc'] = True
                    info['neighbor'] = neighbor
                    info['vpls_id'] = vc_id
                    if mtu:
                        info['mtu'] = mtu
                    info['raw'] = raw

    all_vlans = sorted(set(present_vlans) |
                       set(vlan_descriptions.keys()) |
                       set(vlan_accesses.keys()) |
                       set(vlan_vlanif_info.keys()))

    rows: List[Dict[str, Any]] = []
    for vid in all_vlans:
        info = vlan_vlanif_info.get(vid, {})
        accesses = sorted(list(vlan_accesses.get(vid, set())))
        rows.append({
            'Vlan': vid,
            'Descrição': vlan_descriptions.get(vid, None),
            'Acessos': ', '.join(accesses) if accesses else None,
            'IP': info.get('ip'),
            'MASK4': info.get('mask4'),
            'IPv6': info.get('ipv6'),
            'MASK6': info.get('mask6'),
            'L2VC': 'sim' if info.get('l2vc') else 'não',
            'NEIGHBOR': info.get('neighbor'),
            'VPLS-ID': info.get('vpls_id'),
            'MTU': info.get('mtu', 1500),
            'RAW': 'sim' if info.get('raw') else 'não'
        })
    return rows


def analyze_vlan_contexts_cisco(self) -> List[Dict[str, Any]]:
    vlan_descriptions: Dict[int, str] = {}
    vlan_accesses: Dict[int, set] = {}
    vlan_vlanif_info: Dict[int, Dict[str, Any]] = {}
    present_vlans: set = set()

    current_interface: Optional[str] = None
    in_vlan_block = False
    current_vlan_id: Optional[int] = None

    for raw_line in self.config_lines:
        line = raw_line.strip()

        if line.startswith('vlan '):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                current_vlan_id = int(parts[1])
                present_vlans.add(current_vlan_id)
                in_vlan_block = True
                continue

        if in_vlan_block:
            if line.lower().startswith('name '):
                desc = line.split('name ', 1)[1].strip()
                if current_vlan_id is not None:
                    vlan_descriptions[current_vlan_id] = desc
            if line == '!' or line.startswith('vlan '):
                in_vlan_block = False
                current_vlan_id = None

        if line.startswith('interface '):
            current_interface = line.split('interface ', 1)[1].strip()
            if current_interface.lower().startswith('vlan'):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    present_vlans.add(vid)
                    vlan_vlanif_info.setdefault(vid, {
                        'ip': None, 'mask4': None,
                        'ipv6': None, 'mask6': None,
                        'l2vc': False, 'neighbor': None,
                        'vpls_id': None, 'mtu': 1500, 'raw': False
                    })
                continue

        if current_interface:
            if 'switchport access vlan ' in line.lower():
                try:
                    vlan_id = int(line.split()[-1])
                    present_vlans.add(vlan_id)
                    vlan_accesses.setdefault(vlan_id, set()).add(current_interface)
                except ValueError:
                    pass

            if line.startswith('ip address '):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    parts = line.split()
                    if len(parts) >= 4:
                        info = vlan_vlanif_info.setdefault(vid, {
                            'ip': None, 'mask4': None,
                            'ipv6': None, 'mask6': None,
                            'l2vc': False, 'neighbor': None,
                            'vpls_id': None, 'mtu': 1500, 'raw': False
                        })
                        info['ip'] = parts[2]
                        info['mask4'] = parts[3]

            if line.lower().startswith('ipv6 address '):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    addr = line.split('ipv6 address ', 1)[1].strip()
                    if '/' in addr:
                        ip6, pfx = addr.split('/', 1)
                        info = vlan_vlanif_info.setdefault(vid, {
                            'ip': None, 'mask4': None,
                            'ipv6': None, 'mask6': None,
                            'l2vc': False, 'neighbor': None,
                            'vpls_id': None, 'mtu': 1500, 'raw': False
                        })
                        info['ipv6'] = ip6
                        info['mask6'] = pfx

        if 'xconnect' in line.lower():
            parts = line.split()
            neighbor = None
            vc_id = None
            mtu = None
            raw = (' raw' in line.lower()) or line.lower().endswith('raw')

            for i, t in enumerate(parts):
                if t.lower() == 'xconnect' and i + 1 < len(parts):
                    neighbor = parts[i + 1]
                    for j in range(i + 2, min(i + 6, len(parts))):
                        if parts[j].isdigit():
                            vc_id = int(parts[j])
                            break
                        for j in range(i + 2, len(parts)):
                            if parts[j].lower() == 'mtu' and j + 1 < len(parts) and parts[j + 1].isdigit():
                                mtu = int(parts[j + 1])
                                break
                            break

        if current_interface and current_interface.lower().startswith('vlan'):
            try:
                vid = int(''.join(filter(str.isdigit, current_interface)))
            except ValueError:
                vid = None
            if vid is not None:
                info = vlan_vlanif_info.setdefault(vid, {
                    'ip': None, 'mask4': None,
                    'ipv6': None, 'mask6': None,
                    'l2vc': False, 'neighbor': None,
                    'vpls_id': None, 'mtu': 1500, 'raw': False
                })
                info['l2vc'] = True
                info['neighbor'] = neighbor
                info['vpls_id'] = vc_id
                if mtu:
                    info['mtu'] = mtu
                info['raw'] = raw

    all_vlans = sorted(set(present_vlans) |
                       set(vlan_descriptions.keys()) |
                       set(vlan_accesses.keys()) |
                       set(vlan_vlanif_info.keys()))

    rows: List[Dict[str, Any]] = []
    for vid in all_vlans:
        info = vlan_vlanif_info.get(vid, {})
        accesses = sorted(list(vlan_accesses.get(vid, set())))
        rows.append({
            'Vlan': vid,
            'Descrição': vlan_descriptions.get(vid, None),
            'Acessos': ', '.join(accesses) if accesses else None,
            'IP': info.get('ip'),
            'MASK4': info.get('mask4'),
            'IPv6': info.get('ipv6'),
            'MASK6': info.get('mask6'),
            'L2VC': 'sim' if info.get('l2vc') else 'não',
            'NEIGHBOR': info.get('neighbor'),
            'VPLS-ID': info.get('vpls_id'),
            'MTU': info.get('mtu', 1500),
            'RAW': 'sim' if info.get('raw') else 'não'
        })
    return rows


def analyze_vlan_contexts_mikrotik(self) -> List[Dict[str, Any]]:
    vlan_descriptions: Dict[int, str] = {}
    vlan_accesses: Dict[int, set] = {}
    vlan_vlanif_info: Dict[int, Dict[str, Any]] = {}
    present_vlans: set = set()

    current_interface: Optional[str] = None
    in_vlan_block = False
    current_vlan_id: Optional[int] = None

    for raw_line in self.config_lines:
        line = raw_line.strip()

        if line.startswith('vlan '):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                current_vlan_id = int(parts[1])
                present_vlans.add(current_vlan_id)
                in_vlan_block = True
                continue

        if in_vlan_block:
            if line.lower().startswith('name '):
                desc = line.split('name ', 1)[1].strip()
                if current_vlan_id is not None:
                    vlan_descriptions[current_vlan_id] = desc
            if line == '!' or line.startswith('vlan '):
                in_vlan_block = False
                current_vlan_id = None

        if line.startswith('interface '):
            current_interface = line.split('interface ', 1)[1].strip()
            if current_interface.lower().startswith('vlan'):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    present_vlans.add(vid)
                    vlan_vlanif_info.setdefault(vid, {
                        'ip': None, 'mask4': None,
                        'ipv6': None, 'mask6': None,
                        'l2vc': False, 'neighbor': None,
                        'vpls_id': None, 'mtu': 1500, 'raw': False
                    })
                continue

        if current_interface:
            if 'switchport access vlan ' in line.lower():
                try:
                    vlan_id = int(line.split()[-1])
                    present_vlans.add(vlan_id)
                    vlan_accesses.setdefault(vlan_id, set()).add(current_interface)
                except ValueError:
                    pass

            if line.startswith('ip address '):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    parts = line.split()
                    if len(parts) >= 4:
                        info = vlan_vlanif_info.setdefault(vid, {
                            'ip': None, 'mask4': None,
                            'ipv6': None, 'mask6': None,
                            'l2vc': False, 'neighbor': None,
                            'vpls_id': None, 'mtu': 1500, 'raw': False
                        })
                        info['ip'] = parts[2]
                        info['mask4'] = parts[3]

            if line.lower().startswith('ipv6 address '):
                try:
                    vid = int(''.join(filter(str.isdigit, current_interface)))
                except ValueError:
                    vid = None
                if vid is not None:
                    addr = line.split('ipv6 address ', 1)[1].strip()
                    if '/' in addr:
                        ip6, pfx = addr.split('/', 1)
                        info = vlan_vlanif_info.setdefault(vid, {
                            'ip': None, 'mask4': None,
                            'ipv6': None, 'mask6': None,
                            'l2vc': False, 'neighbor': None,
                            'vpls_id': None, 'mtu': 1500, 'raw': False
                        })
                        info['ipv6'] = ip6
                        info['mask6'] = pfx

        if 'xconnect' in line.lower():
            parts = line.split()
            neighbor = None
            vc_id = None
            mtu = None
            raw = (' raw' in line.lower()) or line.lower().endswith('raw')

            for i, t in enumerate(parts):
                if t.lower() == 'xconnect' and i + 1 < len(parts):
                    neighbor = parts[i + 1]
                    for j in range(i + 2, min(i + 6, len(parts))):
                        if parts[j].isdigit():
                            vc_id = int(parts[j])
                            break
                        for j in range(i + 2, len(parts)):
                            if parts[j].lower() == 'mtu' and j + 1 < len(parts) and parts[j + 1].isdigit():
                                mtu = int(parts[j + 1])
                                break
                            break

        if current_interface and current_interface.lower().startswith('vlan'):
            try:
                vid = int(''.join(filter(str.isdigit, current_interface)))
            except ValueError:
                vid = None
            if vid is not None:
                info = vlan_vlanif_info.setdefault(vid, {
                    'ip': None, 'mask4': None,
                    'ipv6': None, 'mask6': None,
                    'l2vc': False, 'neighbor': None,
                    'vpls_id': None, 'mtu': 1500, 'raw': False
                })
                info['l2vc'] = True
                info['neighbor'] = neighbor
                info['vpls_id'] = vc_id
                if mtu:
                    info['mtu'] = mtu
                info['raw'] = raw

    all_vlans = sorted(set(present_vlans) |
                       set(vlan_descriptions.keys()) |
                       set(vlan_accesses.keys()) |
                       set(vlan_vlanif_info.keys()))

    rows: List[Dict[str, Any]] = []
    for vid in all_vlans:
        info = vlan_vlanif_info.get(vid, {})
        accesses = sorted(list(vlan_accesses.get(vid, set())))
        rows.append({
            'Vlan': vid,
            'Descrição': vlan_descriptions.get(vid, None),
            'Acessos': ', '.join(accesses) if accesses else None,
            'IP': info.get('ip'),
            'MASK4': info.get('mask4'),
            'IPv6': info.get('ipv6'),
            'MASK6': info.get('mask6'),
            'L2VC': 'sim' if info.get('l2vc') else 'não',
            'NEIGHBOR': info.get('neighbor'),
            'VPLS-ID': info.get('vpls_id'),
            'MTU': info.get('mtu', 1500),
            'RAW': 'sim' if info.get('raw') else 'não'
        })
    return rows


def analyze_vlan_contexts(self) -> List[Dict[str, Any]]:
    """Dispatcher para análise unificada de VLAN/L2VPN por vendor."""
    if self.vendor == 'huawei':
        return self.analyze_vlan_contexts_huawei()
    elif self.vendor == 'cisco':
        return self.analyze_vlan_contexts_cisco()
    elif self.vendor == 'mikrotik':
        return self.analyze_vlan_contexts_mikrotik()
    else:
        return []