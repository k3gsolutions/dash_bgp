import requests
from typing import List, Dict, Tuple
import re
import ipaddress

class ConfigService:
    """Serviço para geração de configurações de rede"""
    
    # Padrões de validação
    IPV4_PATTERN = r"(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}"
    IPV6_PATTERN = r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
    
    @staticmethod
    def is_ipv4(prefix: str) -> bool:
        """Verifica se o prefixo é IPv4"""
        network = prefix.split('/')[0] if '/' in prefix else prefix
        return bool(re.match(ConfigService.IPV4_PATTERN, network))
    
    @staticmethod
    def is_ipv6(prefix: str) -> bool:
        """Verifica se o prefixo é IPv6"""
        network = prefix.split('/')[0] if '/' in prefix else prefix
        return bool(re.match(ConfigService.IPV6_PATTERN, network))
    
    @staticmethod
    def get_asn_prefixes(asn: str) -> Tuple[List[str], List[str], str]:
        """Busca prefixos de um ASN usando RIPE API"""
        try:
            asn_number = str(asn).lstrip('AS')
            
            # Buscar prefixos
            response = requests.get(
                f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn_number}",
                timeout=10
            )
            
            # Buscar informações do ASN
            asn_info_response = requests.get(
                f"https://stat.ripe.net/data/as-overview/data.json?resource=AS{asn_number}",
                timeout=10
            )
            
            data = response.json()
            asn_info = asn_info_response.json()
            
            full_asn_name = asn_info.get('data', {}).get('holder', 'Unknown ASN')
            asn_name = full_asn_name.split()[0] if full_asn_name else 'Unknown'
            
            ipv4_prefixes = []
            ipv6_prefixes = []
            
            if 'data' in data and 'prefixes' in data['data']:
                for prefix_entry in data['data']['prefixes']:
                    if 'prefix' in prefix_entry:
                        prefix = prefix_entry['prefix']
                        if ConfigService.is_ipv4(prefix):
                            ipv4_prefixes.append(prefix)
                        elif ConfigService.is_ipv6(prefix):
                            ipv6_prefixes.append(prefix)
            
            return ipv4_prefixes, ipv6_prefixes, asn_name
            
        except Exception as e:
            return [], [], f"Error: {str(e)}"
    
    @staticmethod
    def split_prefix_mask(prefix_cidr: str) -> Tuple[str, str]:
        """Divide um prefixo CIDR em endereço e máscara"""
        if '/' in prefix_cidr:
            prefix, mask = prefix_cidr.split('/')
            return prefix, mask
        return prefix_cidr, ""
    
    @staticmethod
    def prefix_to_rp_name(prefix_cidr: str) -> str:
        """Converte um prefixo em nome de route-policy"""
        if "/" in prefix_cidr:
            net, mask = prefix_cidr.split("/")
        else:
            net, mask = prefix_cidr, ""

        try:
            ip_obj = ipaddress.ip_address(net)
            if ip_obj.version == 4:
                octets = net.split(".")
                octets_form = [o if o != "0" else "000" for o in octets]
                rp_name = "-".join(octets_form + [mask])
            else:
                ip6 = ipaddress.IPv6Address(net)
                exploded = ip6.exploded.split(":")
                rp_name = "-".join(exploded[:3] + [mask])
        except ValueError:
            rp_name = prefix_cidr.replace(".", "-").replace(":", "-").replace("/", "-")

        return rp_name
    
    @staticmethod
    def filter_less_specific_prefixes(prefixes: List[str]) -> List[str]:
        """Filtra prefixos menos específicos"""
        try:
            networks = [ipaddress.ip_network(prefix) for prefix in prefixes]
            filtered = [
                str(net) for net in networks 
                if not any(net.subnet_of(other) for other in networks if net != other)
            ]
            return filtered
        except:
            return prefixes