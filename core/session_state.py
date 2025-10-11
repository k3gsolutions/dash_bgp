import streamlit as st
from typing import Any, Optional

class SessionStateManager:
    """Gerencia o estado da sessão de forma centralizada"""

    @staticmethod
    def initialize():
        """Inicializa veriáveis de estado necessárias"""
        defaults = {
            'current_page': 'home',
            'sidebar_expanded': True,
            'selected_tenant': None,
            'selected_site': None,
            'selected_device': None,
            'last_action': None,
            'cache': {},
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Obtem valor do estado"""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any):
        """Define valor no estado"""
        st.session_state[key] = value
    
    @staticmethod
    def update(updates: dict):
        """Atualiza múltiplos valores"""
        for key, value in updates.items():
            st.session_state[key] = value

    @staticmethod
    def clear_cache():
        """Limpa o cache"""
        st.session_state.cache = {}
    