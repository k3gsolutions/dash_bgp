from typing import List, Dict, Optional

class ServiceNode:
    """Representa um nó na árvore de serviços"""
    
    def __init__(
        self, 
        label: str, 
        value: str, 
        selectable: bool = False,
        children: Optional[List['ServiceNode']] = None
    ):
        self.label = label
        self.value = value
        self.selectable = selectable
        self.children = children or []
    
    def to_dict(self) -> Dict:
        """Converte para dicionário para streamlit-tree-select"""
        node_dict = {
            "label": self.label,
            "value": self.value,
        }
        
        if self.children:
            node_dict["children"] = [child.to_dict() for child in self.children]
        
        return node_dict

class ServiceTreeBuilder:
    """Constrói a árvore de serviços"""
    
    @staticmethod
    def build() -> List[Dict]:
        """Constrói e retorna a árvore de serviços"""
        tree = [
            ServiceNode(
                label="L2VPN",
                value="l2vpn",
                children=[
                    ServiceNode(label="VLAN", value="l2vpn-vlan", selectable=True),
                    ServiceNode(label="Point-to-Point", value="l2vpn-ptp", selectable=True),
                    ServiceNode(label="Point-to-Multipoint", value="l2vpn-ptmp", selectable=True)
                ]
            ),
            ServiceNode(
                label="L3VPN",
                value="l3vpn",
                children=[
                    ServiceNode(label="Cliente Dedicado", value="cl_dedicado", selectable=True),
                    ServiceNode(
                        label="Peering BGP Simples",
                        value="peering_bgp",
                        selectable=False,
                        children=[
                            ServiceNode(label="Cliente de Trânsito", value="bgp_cl_trans", selectable=True),
                            ServiceNode(label="Upstream / Operadora", value="bgp_ups", selectable=True),
                        ]
                    ),
                    ServiceNode(
                        label="Peering BGP Community",
                        value="peering_bgp_comm",
                        children=[
                            ServiceNode(label="Upstream / Operadora (Comm)", value="bgp_ups_comm", selectable=True),
                            ServiceNode(label="Peering CDN", value="peering_cdn_comm", selectable=True),
                            ServiceNode(label="Peering IX", value="bgp_ixbr_comm", selectable=True),
                        ]
                    )
                ]
            ),
        ]
        
        return [node.to_dict() for node in tree]