from typing import List, Dict, Optional, Union, Callable
import streamlit as st
from streamlit_tree_select import tree_select

class ServiceNode:
    """Representa um nó na árvore de serviços"""
    
    def __init__(
        self, 
        label: str, 
        value: str, 
        icon: str = "",
        description: str = "",
        selectable: bool = False,
        children: Optional[List['ServiceNode']] = None
    ):
        self.label = label
        self.value = value
        self.icon = icon
        self.description = description
        self.selectable = selectable
        self.children = children or []
    
    def to_dict(self) -> Dict:
        """Converte para dicionário para streamlit-tree-select"""
        # Adiciona o ícone ao label para melhor visualização
        display_label = f"{self.icon} {self.label}" if self.icon else self.label
        
        node_dict = {
            "label": display_label,
            "value": self.value,
        }
        
        if self.children:
            node_dict["children"] = [child.to_dict() for child in self.children]
        
        return node_dict

class ServiceTreeBuilder:
    """Constrói a árvore de serviços de forma responsiva"""
    
    @staticmethod
    def build() -> List[Dict]:
        """Constrói e retorna a árvore de serviços com ícones e descrições"""
        tree = [
            ServiceNode(
                label="L2VPN",
                value="l2vpn",
                icon="🔄",
                description="Serviços de conectividade de camada 2",
                children=[
                    ServiceNode(
                        label="VLAN", 
                        value="l2vpn-vlan", 
                        icon="🏷️",
                        description="Configuração de VLAN em um dispositivo",
                        selectable=True
                    ),
                    ServiceNode(
                        label="Point-to-Point", 
                        value="l2vpn-ptp", 
                        icon="🔌",
                        description="Conexão L2 entre dois sites",
                        selectable=True
                    ),
                    ServiceNode(
                        label="Point-to-Multipoint", 
                        value="l2vpn-ptmp", 
                        icon="🌐",
                        description="VPLS conectando múltiplos sites",
                        selectable=True
                    )
                ]
            ),
            ServiceNode(
                label="L3VPN",
                value="l3vpn",
                icon="🌍",
                description="Serviços de conectividade de camada 3",
                children=[
                    ServiceNode(
                        label="Cliente Dedicado", 
                        value="cl_dedicado", 
                        icon="👤",
                        description="Configuração de enlace L3 dedicado",
                        selectable=True
                    ),
                    ServiceNode(
                        label="Peering BGP Simples",
                        value="peering_bgp",
                        icon="🔄",
                        description="Configurações de BGP sem comunidades",
                        selectable=False,
                        children=[
                            ServiceNode(
                                label="Cliente de Trânsito", 
                                value="bgp_cl_trans", 
                                icon="🚦",
                                description="Peering BGP para cliente de trânsito",
                                selectable=True
                            ),
                            ServiceNode(
                                label="Upstream / Operadora", 
                                value="bgp_ups", 
                                icon="📡",
                                description="Peering BGP com operadora",
                                selectable=True
                            ),
                        ]
                    ),
                    ServiceNode(
                        label="Peering BGP Community",
                        value="peering_bgp_comm",
                        icon="🔄",
                        description="Configurações de BGP com comunidades",
                        children=[
                            ServiceNode(
                                label="Upstream / Operadora (Comm)", 
                                value="bgp_ups_comm", 
                                icon="📡",
                                description="Peering BGP com operadora usando comunidades",
                                selectable=True
                            ),
                            ServiceNode(
                                label="Peering CDN", 
                                value="peering_cdn_comm", 
                                icon="📊",
                                description="Configuração de peering com CDN",
                                selectable=True
                            ),
                            ServiceNode(
                                label="Peering IX", 
                                value="bgp_ixbr_comm", 
                                icon="🔄",
                                description="Configuração para IX (Internet Exchange)",
                                selectable=True
                            ),
                        ]
                    )
                ]
            ),
        ]
        
        return [node.to_dict() for node in tree]
    
    @staticmethod
    def render_responsive_tree(container=None, on_select: Callable = None):
        """Renderiza a árvore de serviços de forma responsiva
        
        Args:
            container: Container do Streamlit onde a árvore será renderizada
            on_select: Função de callback para quando um serviço for selecionado
        """
        # Usa o container fornecido ou o st diretamente
        ctx = container if container else st
        
        # Constrói a árvore
        nodes = ServiceTreeBuilder.build()
        
        # Detecta o tamanho da tela (usando session_state como proxy)
        is_mobile = st.session_state.get('is_mobile', False)
        
        # Renderiza a árvore de forma responsiva
        if is_mobile:
            # Versão compacta para dispositivos móveis
            ctx.markdown("### 📱 Selecione um Serviço")
            
            # Agrupa os serviços por categoria
            categories = {}
            for node in nodes:
                category = node["label"]
                services = []
                
                if "children" in node:
                    for child in node["children"]:
                        if "children" in child:
                            # Subnível adicional
                            for subchild in child["children"]:
                                services.append((subchild["label"], subchild["value"]))
                        else:
                            services.append((child["label"], child["value"]))
                
                categories[category] = services
            
            # Cria um seletor de duas etapas
            category = ctx.selectbox("Categoria", options=list(categories.keys()))
            
            if category and categories[category]:
                service_options = categories[category]
                service_labels = [label for label, _ in service_options]
                service_values = [value for _, value in service_options]
                
                selected_index = ctx.selectbox("Serviço", options=range(len(service_labels)), 
                                              format_func=lambda i: service_labels[i])
                
                if selected_index is not None:
                    selected_value = service_values[selected_index]
                    # Simula o formato de retorno do tree_select
                    selected_dict = {"checked": [selected_value]}
                    
                    if on_select:
                        on_select(selected_dict)
                    
                    return selected_dict
        else:
            # Versão completa para desktop
            selected_dict = tree_select(
                nodes=nodes,
                show_expand_all=True,
                key="service_tree"
            )
            
            if on_select and selected_dict and selected_dict.get("checked"):
                on_select(selected_dict)
            
            return selected_dict
        
        return {"checked": []}