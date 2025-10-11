import streamlit as st
from typing import Dict, Callable
from core.session_state import SessionStateManager

class PageRouter:
    """Gerencia o roteamento de páginas"""
    
    def __init__(self):
        self.state = SessionStateManager()
        self.pages: Dict[str, Callable] = {}
    
    def register(self, page_id: str, render_func: Callable):
        """Registra uma página"""
        self.pages[page_id] = render_func
    
    def render_current_page(self):
        """Renderiza a página atual"""
        current_page = self.state.get('current_page', 'home')
        
        if current_page in self.pages:
            # Renderiza a página em um container
            with st.container():
                self.pages[current_page]()
        else:
            st.error(f"Página '{current_page}' não encontrada")
            st.info("Retornando para a página inicial...")
            self.state.set('current_page', 'home')
            st.rerun()