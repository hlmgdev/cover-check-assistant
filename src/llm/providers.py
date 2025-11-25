"""Implementações dos providers de LLM."""

import os
from typing import Optional
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import AzureChatOpenAI, ChatOllama, ChatOpenAI as ChatOpenAICommunity
from langchain_core.language_models import BaseChatModel


class ProvedorLLM(str, Enum):
    """Enum dos provedores de LLM suportados."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENROUTER = "openrouter"


def criar_llm_openai() -> Optional[ChatOpenAI]:
    """Cria instância do LLM OpenAI."""
    chave_api = os.getenv("OPENAI_API_KEY")
    if not chave_api:
        return None
    
    modelo = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperatura = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))
    
    return ChatOpenAI(
        model=modelo,
        temperature=temperatura,
        max_tokens=max_tokens,
        api_key=chave_api
    )


def criar_llm_anthropic() -> Optional[ChatAnthropic]:
    """Cria instância do LLM Anthropic (Claude)."""
    chave_api = os.getenv("ANTHROPIC_API_KEY")
    if not chave_api:
        return None
    
    modelo = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    temperatura = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000"))
    
    return ChatAnthropic(
        model=modelo,
        temperature=temperatura,
        max_tokens=max_tokens,
        api_key=chave_api
    )


def criar_llm_google() -> Optional[ChatGoogleGenerativeAI]:
    """Cria instância do LLM Google (Gemini)."""
    chave_api = os.getenv("GOOGLE_API_KEY")
    if not chave_api:
        return None
    
    modelo = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
    temperatura = float(os.getenv("GOOGLE_TEMPERATURE", "0.7"))
    
    return ChatGoogleGenerativeAI(
        model=modelo,
        temperature=temperatura,
        google_api_key=chave_api
    )


def criar_llm_azure() -> Optional[AzureChatOpenAI]:
    """Cria instância do LLM Azure OpenAI."""
    chave_api = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    versao_api = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not chave_api or not endpoint:
        return None
    
    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment,
        api_version=versao_api,
        api_key=chave_api,
        temperature=0.7
    )


def criar_llm_ollama() -> Optional[ChatOllama]:
    """Cria instância do LLM Ollama (local)."""
    url_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    modelo = os.getenv("OLLAMA_MODEL", "llama3.2")
    temperatura = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    
    return ChatOllama(
        base_url=url_base,
        model=modelo,
        temperature=temperatura
    )


def criar_llm_groq() -> Optional[ChatOpenAI]:
    """Cria instância do LLM Groq."""
    chave_api = os.getenv("GROQ_API_KEY")
    if not chave_api:
        return None
    
    modelo = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    temperatura = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "4000"))
    
    # Groq usa a API OpenAI-compatible
    return ChatOpenAI(
        model=modelo,
        temperature=temperatura,
        max_tokens=max_tokens,
        api_key=chave_api,
        base_url="https://api.groq.com/openai/v1"
    )


def criar_llm_openrouter() -> Optional[ChatOpenAI]:
    """Cria instância do LLM OpenRouter."""
    chave_api = os.getenv("OPENROUTER_API_KEY")
    if not chave_api:
        return None
    
    modelo = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    temperatura = float(os.getenv("OPENROUTER_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "4000"))
    
    # OpenRouter usa a API OpenAI-compatible
    return ChatOpenAI(
        model=modelo,
        temperature=temperatura,
        max_tokens=max_tokens,
        api_key=chave_api,
        base_url="https://openrouter.ai/api/v1"
    )


def obter_llm_para_provedor(provedor: str) -> Optional[BaseChatModel]:
    """
    Retorna uma instância de LLM baseada no provedor especificado.
    
    Args:
        provedor: Nome do provedor (openai, anthropic, google, azure, ollama, groq, openrouter)
    
    Returns:
        Instância do LLM ou None se não configurado
    """
    provedor_lower = provedor.lower()
    
    if provedor_lower == ProvedorLLM.OPENAI:
        return criar_llm_openai()
    elif provedor_lower == ProvedorLLM.ANTHROPIC:
        return criar_llm_anthropic()
    elif provedor_lower == ProvedorLLM.GOOGLE:
        return criar_llm_google()
    elif provedor_lower == ProvedorLLM.AZURE:
        return criar_llm_azure()
    elif provedor_lower == ProvedorLLM.OLLAMA:
        return criar_llm_ollama()
    elif provedor_lower == ProvedorLLM.GROQ:
        return criar_llm_groq()
    elif provedor_lower == ProvedorLLM.OPENROUTER:
        return criar_llm_openrouter()
    else:
        raise ValueError(f"Provedor não suportado: {provedor}")
