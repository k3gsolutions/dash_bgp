from jinja2 import Environment, BaseLoader, TemplateNotFound
from typing import Dict

class HierarchicalLoader(BaseLoader):
    """Carregador customizado para templates hierárquicos"""
    
    def __init__(self, template_file: str):
        with open(template_file, "r", encoding='utf-8') as f:
            self.data = f.read()
        self.templates = self._parse_templates(self.data)

    def _parse_templates(self, data: str) -> Dict[str, str]:
        """Parse os templates do arquivo"""
        templates = {}
        parts = data.split('---')
        
        for part in parts:
            if not part.strip():
                continue
            
            lines = part.strip().splitlines()
            if not lines:
                continue
            
            # Primeira linha é o caminho do template
            template_path = lines[0].strip()
            # Restante é o conteúdo
            template_content = "\n".join(lines[1:]).strip()
            templates[template_path] = template_content
        
        return templates

    def get_source(self, environment, template):
        """Obtém o código fonte de um template"""
        if template in self.templates:
            source = self.templates[template]
            return source, None, lambda: True
        else:
            raise TemplateNotFound(template)

class TemplateService:
    """Serviço para gerenciamento de templates"""
    
    def __init__(self, template_file: str = 'templates/templates.txt'):
        loader = HierarchicalLoader(template_file)
        self.env = Environment(loader=loader)
    
    def render_template(self, template_path: str, **context) -> str:
        """Renderiza um template com o contexto fornecido"""
        try:
            template = self.env.get_template(template_path)
            return template.render(**context)
        except TemplateNotFound:
            raise ValueError(f"Template '{template_path}' não encontrado")
        except Exception as e:
            raise ValueError(f"Erro ao renderizar template: {str(e)}")
    
    def list_templates(self) -> list:
        """Lista todos os templates disponíveis"""
        return list(self.env.loader.templates.keys())