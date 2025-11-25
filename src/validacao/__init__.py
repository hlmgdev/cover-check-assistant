"""Módulo de validação de ambiente e repositório."""

from .git import verificar_repositorio_git, detectar_branch_base, obter_branch_atual
from .utilidades import (
    executar_comando,
    imprimir_cabecalho,
    imprimir_sucesso,
    imprimir_erro,
    imprimir_aviso,
    imprimir_info,
    Cores
)

__all__ = [
    "verificar_repositorio_git",
    "detectar_branch_base",
    "obter_branch_atual",
    "executar_comando",
    "imprimir_cabecalho",
    "imprimir_sucesso",
    "imprimir_erro",
    "imprimir_aviso",
    "imprimir_info",
    "Cores"
]

