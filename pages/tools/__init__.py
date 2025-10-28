"""
Módulo de ferramentas do dashboard
"""

# Importações das ferramentas disponíveis
try:
    from . import config_analyzer
except ImportError:
    config_analyzer = None

__all__ = ['config_analyzer']