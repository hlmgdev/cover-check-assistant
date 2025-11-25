"""Parser para código C# e testes."""

from typing import List, Dict, Any
import re


class ParserCodigo:
    """Parser para analisar código C# e extrair informações."""
    
    @staticmethod
    def extrair_classes(codigo: str) -> List[Dict[str, Any]]:
        """
        Extrai informações sobre classes do código C#.
        
        Args:
            codigo: Código fonte C#
        
        Returns:
            Lista de dicionários com informações das classes
        """
        classes = []
        linhas = codigo.split('\n')
        
        classe_atual = None
        inicio_classe = None
        contador_chaves = 0
        
        for i, linha in enumerate(linhas, 1):
            linha_limpa = linha.strip()
            
            # Detecta início de classe
            if re.match(r'^\s*(public\s+)?(abstract\s+)?(sealed\s+)?class\s+\w+', linha_limpa):
                if classe_atual:
                    classes.append(classe_atual)
                
                nome_classe = re.search(r'class\s+(\w+)', linha_limpa).group(1)
                classe_atual = {
                    "nome": nome_classe,
                    "linha_inicio": i,
                    "linha_fim": None,
                    "metodos": []
                }
                inicio_classe = i
                contador_chaves = linha_limpa.count('{') - linha_limpa.count('}')
            
            elif classe_atual:
                contador_chaves += linha_limpa.count('{') - linha_limpa.count('}')
                
                # Detecta métodos
                if re.match(r'^\s*public\s+.*\(', linha_limpa):
                    match_metodo = re.search(r'(\w+)\s*\(', linha_limpa)
                    if match_metodo:
                        nome_metodo = match_metodo.group(1)
                        classe_atual["metodos"].append({
                            "nome": nome_metodo,
                            "linha": i
                        })
                
                # Fim da classe
                if contador_chaves == 0 and '{' not in linha_limpa:
                    classe_atual["linha_fim"] = i
                    classes.append(classe_atual)
                    classe_atual = None
        
        if classe_atual:
            classes.append(classe_atual)
        
        return classes
    
    @staticmethod
    def extrair_metodos(codigo: str, nome_classe: str = None) -> List[Dict[str, Any]]:
        """
        Extrai métodos do código.
        
        Args:
            codigo: Código fonte
            nome_classe: Nome da classe (opcional, para filtrar)
        
        Returns:
            Lista de métodos encontrados
        """
        metodos = []
        linhas = codigo.split('\n')
        
        for i, linha in enumerate(linhas, 1):
            linha_limpa = linha.strip()
            
            # Padrão para métodos públicos
            if re.match(r'^\s*public\s+.*\(', linha_limpa):
                match_metodo = re.search(r'(\w+)\s*\(', linha_limpa)
                if match_metodo:
                    nome_metodo = match_metodo.group(1)
                    metodos.append({
                        "nome": nome_metodo,
                        "linha": i,
                        "assinatura": linha_limpa
                    })
        
        return metodos
    
    @staticmethod
    def extrair_declaracoes_using(codigo: str) -> List[str]:
        """
        Extrai declarações 'using' do código.
        
        Args:
            codigo: Código fonte
        
        Returns:
            Lista de namespaces importados
        """
        usings = []
        for linha in codigo.split('\n'):
            linha_limpa = linha.strip()
            if linha_limpa.startswith('using ') and linha_limpa.endswith(';'):
                namespace = linha_limpa[6:-1].strip()
                usings.append(namespace)
        return usings


# Aliases para compatibilidade
CodeParser = ParserCodigo
extract_classes = ParserCodigo.extrair_classes
extract_methods = ParserCodigo.extrair_metodos
extract_using_statements = ParserCodigo.extrair_declaracoes_using
