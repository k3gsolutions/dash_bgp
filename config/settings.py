import os
from dataclasses import dataclass
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

@dataclass
class NetboxConfig:
    url: str
    api_token: str
    
    @classmethod
    def from_env(cls):
        return cls(
            url=os.getenv('NETBOX_URL'),
            api_token=os.getenv('API_TOKEN')
        )

@dataclass
class MenuItem:
    """Representa um item do menu"""
    id: str
    label: str
    icon: str
    page: str
    children: List['MenuItem'] = None

    def has_children(self) -> bool:
        return self.children is not None and len(self.children) > 0

class AppConfig:
    """Configurações da aplicaçãao"""

    # Configuração do Netbox
    NETBOX = NetboxConfig.from_env()

    # Estrutura do menu
    MENU_STRUCTURE = [
        MenuItem(
            id="home",
            label="Início",
            icon="🏠",
            page="home"
        ),
        MenuItem(
            id="cadastro",
            label="Cadastro",
            icon="📝",
            page=None,
            children=[
                MenuItem(id="cadastro_clientes", label="Clientes", icon="👥", page="cadastro.clientes"),
                MenuItem(id="cadastro_sites", label="Sites", icon="📍", page="cadastro.sites"),
                MenuItem(id="cadastro_dispositivos", label="Dispositivos", icon="🖥️", page="cadastro.dispositivos"),
                MenuItem(id="cadastro_circuitos", label="Circuitos", icon="🔌", page="cadastro.circuitos"),
            ]
        ),
        MenuItem(
            id="consulta",
            label="Consulta",
            icon="🔍",
            page=None,
            children=[
                MenuItem(id="consulta_cliente", label="Cliente", icon="👤", page="consulta.cliente"),
                MenuItem(id="consulta_dispositivo", label="Dispositivo", icon="💻", page="consulta.dispositivo"),
            ]
        ),
        MenuItem(
            id="gera_config",
            label="Gerar Configuração",
            icon="⚙️",
            page="gera_config"
        ),
        MenuItem(
            id="tools",
            label="Ferramentas",
            icon="🛠️",
            page=None,
            children=[
                MenuItem(id="tool_traceroute", label="Traceroute", icon="🗺️", page="tools.traceroute"),
                MenuItem(id="tool_whois", label="Whois", icon="ℹ️", page="tools.whois"),
                MenuItem(id="tool_looking_glass", label="Looking Glass", icon="🔭", page="tools.looking_glass"),
                MenuItem(id="tool_ping", label="Ping", icon="📡", page="tools.ping"),
                MenuItem(id="tool_ipcalc", label="IP Calculator", icon="🔢", page="tools.ipcalc"),
            ]
        ),
    ]

    # Configurações de estilo
    SIDEBAR_WIDTH_COLLAPSED = 80
    SIDEBAR_WIDTH_EXPANDED = 280

    # Configurações de cache
    CACHE_TTL = 3600 # 1hora
