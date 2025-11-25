"""Definição do estado do agente."""

from typing import TypedDict, List, Dict, Optional, Any


class EstadoAgente(TypedDict):
    """
    Estado compartilhado do agente durante a execução.
    
    Atributos:
        codigo_fonte: Código fonte C# a ser testado
        testes_existentes: Testes unitários existentes
        testes_gerados: Testes gerados pelo agente
        percentual_cobertura: Percentual de cobertura atual
        meta_cobertura: Meta de cobertura desejada
        iteracao: Número da iteração atual
        max_iteracoes: Número máximo de iterações permitidas
        historico: Histórico de ações e resultados
        erros: Lista de erros encontrados
        caminho_arquivo: Caminho do arquivo sendo processado
        caminho_projeto: Caminho do projeto .NET
        deve_continuar: Flag indicando se deve continuar o loop
    """
    codigo_fonte: str
    testes_existentes: str
    testes_gerados: List[str]
    percentual_cobertura: float
    meta_cobertura: float
    iteracao: int
    max_iteracoes: int
    historico: List[Dict[str, Any]]
    erros: List[str]
    caminho_arquivo: Optional[str]
    caminho_projeto: Optional[str]
    deve_continuar: bool

# Alias para compatibilidade
AgentState = EstadoAgente
