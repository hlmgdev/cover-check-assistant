"""Definição do grafo LangGraph do agente."""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import EstadoAgente
from .nodes import (
    no_validar_ambiente,
    no_analisar_codigo,
    no_gerar_testes,
    no_validar_testes,
    no_verificar_cobertura
)


def deve_continuar(estado: EstadoAgente) -> Literal["continuar", "fim"]:
    """
    Função de decisão: decide se continua ou termina o loop.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        "continuar" para continuar, "fim" para terminar
    """
    deve_continuar_flag = estado.get("deve_continuar", False)
    
    if deve_continuar_flag:
        return "continuar"
    else:
        return "fim"


def incrementar_iteracao(estado: EstadoAgente) -> dict:
    """
    Incrementa o contador de iterações.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Estado atualizado com iteração incrementada
    """
    iteracao_atual = estado.get("iteracao", 0)
    return {
        "iteracao": iteracao_atual + 1
    }


def criar_grafo_agente():
    """
    Cria e retorna o grafo do agente.
    
    Returns:
        Grafo LangGraph configurado
    """
    # Cria o grafo
    workflow = StateGraph(EstadoAgente)
    
    # Adiciona os nós
    workflow.add_node("validar_ambiente", no_validar_ambiente)
    workflow.add_node("analisar_codigo", no_analisar_codigo)
    workflow.add_node("gerar_testes", no_gerar_testes)
    workflow.add_node("validar_testes", no_validar_testes)
    workflow.add_node("verificar_cobertura", no_verificar_cobertura)
    workflow.add_node("incrementar_iteracao", incrementar_iteracao)
    
    # Define o ponto de entrada (primeira etapa: validação)
    workflow.set_entry_point("validar_ambiente")
    
    # Define o fluxo
    workflow.add_edge("validar_ambiente", "analisar_codigo")
    workflow.add_edge("analisar_codigo", "gerar_testes")
    workflow.add_edge("gerar_testes", "validar_testes")
    workflow.add_edge("validar_testes", "verificar_cobertura")
    
    # Adiciona condição após verificar cobertura
    workflow.add_conditional_edges(
        "verificar_cobertura",
        deve_continuar,
        {
            "continuar": "incrementar_iteracao",
            "fim": END
        }
    )
    
    # Loop: incrementa iteração e volta para gerar mais testes
    workflow.add_edge("incrementar_iteracao", "gerar_testes")
    
    # Compila o grafo com checkpoint para memória
    memoria = MemorySaver()
    app = workflow.compile(checkpointer=memoria)
    
    return app


# Alias para compatibilidade
create_agent_graph = criar_grafo_agente
