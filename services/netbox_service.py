import requests
from typing import List, Dict, Optional
from config.settings import AppConfig
from core.session_state import SessionStateManager
import streamlit as st

class NetboxService:
    """Serviço para interação com a API do Netbox"""
    
    def __init__(self):
        self.config = AppConfig.NETBOX
        self.base_url = self.config.url
        self.headers = {
            "Authorization": f"Token {self.config.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.state = SessionStateManager()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Faz requisição para a API do Netbox"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao conectar com Netbox: {str(e)}")
            return {"results": [], "count": 0}
    
    def _get_paginated_results(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """Obtém todos os resultados paginados"""
        all_results = []
        next_url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        while next_url:
            try:
                response = requests.get(next_url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                all_results.extend(data.get("results", []))
                next_url = data.get("next")
                params = None  # Params já estão na next_url
            except requests.exceptions.RequestException as e:
                st.error(f"Erro ao buscar dados paginados: {str(e)}")
                break
        
        return all_results
    
    # Métodos para Tenants
    def get_tenants(self) -> List[Dict]:
        """Busca todos os tenants"""
        cache_key = 'tenants_list'
        cached = self.state.get('cache', {}).get(cache_key)
        
        if cached:
            return cached
        
        results = self._get_paginated_results("tenancy/tenants/")
        
        # Salvar no cache
        cache = self.state.get('cache', {})
        cache[cache_key] = results
        self.state.set('cache', cache)
        
        return results
    
    def get_tenant_by_id(self, tenant_id: int) -> Optional[Dict]:
        """Busca tenant por ID"""
        data = self._make_request(f"tenancy/tenants/{tenant_id}/")
        return data if data.get('id') else None
    
    # Métodos para Sites
    def get_sites(self, tenant_id: Optional[int] = None) -> List[Dict]:
        """Busca sites, opcionalmente filtrados por tenant"""
        params = {"tenant_id": tenant_id} if tenant_id else None
        return self._get_paginated_results("dcim/sites/", params=params)
    
    def get_site_by_id(self, site_id: int) -> Optional[Dict]:
        """Busca site por ID"""
        data = self._make_request(f"dcim/sites/{site_id}/")
        return data if data.get('id') else None
    
    # Métodos para Dispositivos
    def get_devices(self, site_id: Optional[int] = None, tenant_id: Optional[int] = None) -> List[Dict]:
        """Busca dispositivos, com filtros opcionais"""
        params = {}
        if site_id:
            params['site_id'] = site_id
        if tenant_id:
            params['tenant_id'] = tenant_id
        
        return self._get_paginated_results("dcim/devices/", params=params)
    
    def get_device_by_id(self, device_id: int) -> Optional[Dict]:
        """Busca dispositivo por ID"""
        data = self._make_request(f"dcim/devices/{device_id}/")
        return data if data.get('id') else None
    
    def get_device_interfaces(self, device_id: int) -> List[Dict]:
        """Busca interfaces de um dispositivo"""
        return self._get_paginated_results(f"dcim/interfaces/", params={"device_id": device_id})
    
    # Métodos para IPs
    def get_device_primary_ip(self, device_id: int) -> Optional[str]:
        """Obtém o IP primário de um dispositivo"""
        device = self.get_device_by_id(device_id)
        if not device:
            return None
        
        primary_ip = device.get('primary_ip')
        if not primary_ip:
            return None
        
        # Buscar detalhes do IP
        ip_id = primary_ip.get('id')
        if not ip_id:
            return None
        
        ip_data = self._make_request(f"ipam/ip-addresses/{ip_id}/")
        address = ip_data.get('address', 'N/A')
        
        # Retornar apenas o IP sem máscara
        return address.split('/')[0] if '/' in address else address
    
    # Métodos auxiliares
    def clear_cache(self):
        """Limpa o cache do serviço"""
        self.state.set('cache', {})