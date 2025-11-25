"""Factory para criar instâncias de LLM."""

import os
from typing import Optional
from langchain_core.language_models import BaseChatModel

from .providers import obter_llm_para_provedor, ProvedorLLM


def criar_llm(provedor: Optional[str] = None) -> Optional[BaseChatModel]:
    """
    Cria uma instância de LLM baseada na configuração.
    
    Args:
        provedor: Provedor específico a usar. Se None, usa LLM_PROVIDER do .env
    
    Returns:
        Instância do LLM configurada ou None se não configurado
    """
    if provedor is None:
        provedor = os.getenv("LLM_PROVIDER", "openai")
    
    try:
        llm = obter_llm_para_provedor(provedor)
        if llm is None:
            print(f"⚠️  Provedor '{provedor}' não está configurado corretamente.")
            print(f"   Verifique as variáveis de ambiente no arquivo .env")
        return llm
    except ValueError as e:
        print(f"❌ Erro ao criar LLM: {e}")
        return None
