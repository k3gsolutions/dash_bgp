from typing import List, Dict, Optional, Union, Callable
import streamlit as st
from streamlit_tree_select import tree_select
import re

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
    
    def is_leaf(self) -> bool:
        """Verifica se o nó é uma folha (não tem filhos)"""
        return not self.children or len(self.children) == 0
    
    def to_dict(self) -> Dict:
        """Converte para dicionário para streamlit-tree-select"""
        # Adiciona o ícone ao label para melhor visualização
        display_label = f"{self.icon} {self.label}" if self.icon else self.label
        
        node_dict = {
            "label": display_label,
            "value": self.value,
        }
        
        if self.children:
            # Se tem filhos, não mostra checkbox
            node_dict["no_checkbox"] = True
            node_dict["children"] = [child.to_dict() for child in self.children]
        else:
            # Se é folha, permite seleção
            node_dict["disabled"] = not self.selectable
        
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
    def detect_mobile():
        """Detecta se o dispositivo é móvel baseado na largura da tela
        
        Em uma implementação real, isso seria feito com JavaScript ou
        usando o user-agent. Para simplificar, usamos uma variável na session_state.
        """
        # Inicializa a detecção de dispositivo móvel se não existir
        if 'is_mobile' not in st.session_state:
            # Por padrão, assumimos desktop
            st.session_state['is_mobile'] = False
            
            # Em uma implementação real, isso seria feito com JavaScript
            # Para fins de demonstração, podemos usar um valor fixo ou
            # permitir que o usuário alterne manualmente
            
        return st.session_state.get('is_mobile', False)
    
    @staticmethod
    def render_responsive_tree(container=None, on_select: Callable = None, show_toggle=True):
        """Renderiza a árvore de serviços de forma responsiva
        
        Args:
            container: Container do Streamlit onde a árvore será renderizada
            on_select: Função de callback para quando um serviço for selecionado
            show_toggle: Se deve mostrar o botão para alternar entre visualizações
        """
        # Usa o container fornecido ou o st diretamente
        ctx = container if container else st
        
        # Detecta o dispositivo
        is_mobile = ServiceTreeBuilder.detect_mobile()
        
        # Opção para alternar entre visualizações (para testes)
        if show_toggle:
            mobile_toggle = ctx.checkbox("📱 Modo Compacto", 
                                        value=is_mobile,
                                        help="Alterne entre visualização completa e compacta")
            
            if mobile_toggle != is_mobile:
                st.session_state['is_mobile'] = mobile_toggle
                st.rerun()
        
        # Constrói a árvore
        nodes = ServiceTreeBuilder.build()
        
        # Aplica estilo CSS para reduzir o tamanho da fonte
        ctx.markdown("""
            <style>
                /* Reduz o tamanho da fonte de todos os nós */
                .tree-select-container .tree-node-label,
                .tree-select-container .tree-node-parent > div {
                    font-size: 10px !important;
                }
                
                /* Ajusta o espaçamento vertical para melhor legibilidade */
                .tree-select-container .tree-node {
                    padding-top: 2px !important;
                    padding-bottom: 2px !important;
                }
                
                /* Ajusta o tamanho dos checkboxes e ícones de expansão */
                .tree-select-container .tree-node-checkbox,
                .tree-select-container .tree-node-parent > div > svg {
                    transform: scale(0.8);
                }
                
                /* Ajusta o alinhamento vertical dos ícones com o texto */
                .tree-select-container .tree-node-parent > div > svg {
                    margin-top: -1px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Renderiza a árvore de forma responsiva
        if is_mobile:
            # Versão compacta para dispositivos móveis
            with ctx.container():
                # Agrupa os serviços por categoria
                categories = {}
                for node in nodes:
                    # Remove emojis do label para exibição limpa
                    category_label = node["label"]
                    category_label = re.sub(r'[^\w\s]', '', category_label).strip()
                    
                    services = []
                    
                    if "children" in node:
                        for child in node["children"]:
                            child_label = re.sub(r'[^\w\s]', '', child["label"]).strip()
                            
                            if "children" in child:
                                # Subnível adicional - adiciona o nome do pai como prefixo
                                for subchild in child["children"]:
                                    # Verifica se o item é selecionável (não está desabilitado)
                                    if not subchild.get("disabled", False):
                                        subchild_label = re.sub(r'[^\w\s]', '', subchild["label"]).strip()
                                        services.append((f"{child_label} - {subchild_label}", subchild["value"]))
                            else:
                                # Verifica se o item é selecionável (não está desabilitado)
                                if not child.get("disabled", False):
                                    services.append((child_label, child["value"]))
                    
                    # Só adiciona a categoria se tiver serviços selecionáveis
                    if services:
                        categories[category_label] = services
                
                # Cria um seletor de duas etapas com estilo melhorado
                col1, col2 = ctx.columns(2)
                
                # Adiciona estilo CSS para os seletores móveis
                ctx.markdown("""
                    <style>
                        /* Reduz o tamanho da fonte dos seletores */
                        .stSelectbox > label {
                            font-size: 10px !important;
                        }
                        .stSelectbox > div > div {
                            font-size: 10px !important;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                with col1:
                    category = st.selectbox("Categoria", 
                                          options=list(categories.keys()),
                                          key="service_category")
                
                if category and categories[category]:
                    service_options = categories[category]
                    service_labels = [label for label, _ in service_options]
                    service_values = [value for _, value in service_options]
                    
                    with col2:
                        selected_index = st.selectbox("Serviço", 
                                                    options=range(len(service_labels)), 
                                                    format_func=lambda i: service_labels[i],
                                                    key="service_option")
                    
                    if selected_index is not None:
                        selected_value = service_values[selected_index]
                        
                        # Exibe descrição do serviço selecionado
                        service_info = None
                        for node in nodes:
                            for child in node.get("children", []):
                                if child.get("value") == selected_value:
                                    service_info = child
                                    break
                                for subchild in child.get("children", []):
                                    if subchild.get("value") == selected_value:
                                        service_info = subchild
                                        break
                        
                        # Simula o formato de retorno do tree_select
                        selected_dict = {"checked": [selected_value]}
                        
                        if on_select:
                            on_select(selected_dict)
                        
                        return selected_dict
        else:
            # Versão completa para desktop
            with ctx.container():
                # Garantir que apenas um item pode ser selecionado
                if 'last_selected' not in st.session_state:
                    st.session_state['last_selected'] = None
                
                selected_dict = tree_select(
                    nodes=nodes,
                    show_expand_all=True,
                    key="service_tree",
                    check_model="radio",  # Força seleção única
                    only_leaf_checkboxes=True  # Mostra checkboxes apenas em nós folha
                )
                
                # Validar seleção
                if selected_dict and selected_dict.get("checked"):
                    selected_value = selected_dict["checked"][0]
                    
                    # Verifica se o item selecionado é um nó folha válido
                    def is_valid_leaf(nodes, value):
                        for node in nodes:
                            if "children" in node:
                                if is_valid_leaf(node["children"], value):
                                    return True
                            elif not node.get("disabled", False) and node["value"] == value:
                                return True
                        return False
                    
                    if is_valid_leaf(nodes, selected_value):
                        # Atualizar último item selecionado
                        st.session_state['last_selected'] = selected_value
                        
                        if on_select:
                            on_select(selected_dict)
                    else:
                        # Se selecionou um nó pai, limpa a seleção
                        selected_dict["checked"] = []
                
                return selected_dict
        
        return {"checked": []}