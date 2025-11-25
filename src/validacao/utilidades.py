"""Utilitários para validação e execução de comandos."""

import sys
import subprocess
from typing import List, Optional
from pathlib import Path


class Cores:
    """Cores ANSI para output no console."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def imprimir_cabecalho(mensagem: str):
    """Imprime um cabeçalho formatado."""
    print(f"\n{Cores.HEADER}{Cores.BOLD}{'=' * 80}{Cores.ENDC}")
    print(f"{Cores.HEADER}{Cores.BOLD}{mensagem.center(80)}{Cores.ENDC}")
    print(f"{Cores.HEADER}{Cores.BOLD}{'=' * 80}{Cores.ENDC}\n")


def imprimir_sucesso(mensagem: str):
    """Imprime mensagem de sucesso."""
    print(f"{Cores.OKGREEN}✓ {mensagem}{Cores.ENDC}")


def imprimir_erro(mensagem: str):
    """Imprime mensagem de erro."""
    print(f"{Cores.FAIL}✗ {mensagem}{Cores.ENDC}", file=sys.stderr)


def imprimir_aviso(mensagem: str):
    """Imprime mensagem de aviso."""
    print(f"{Cores.WARNING}⚠ {mensagem}{Cores.ENDC}")


def imprimir_info(mensagem: str):
    """Imprime mensagem informativa."""
    print(f"{Cores.OKBLUE}ℹ {mensagem}{Cores.ENDC}")


def executar_comando(
    comando: List[str],
    diretorio: Optional[Path] = None,
    verificar: bool = True
) -> subprocess.CompletedProcess:
    """
    Executa um comando e retorna o resultado.
    
    Args:
        comando: Lista com comando e argumentos
        diretorio: Diretório de trabalho (opcional)
        verificar: Se True, lança exceção em caso de erro
    
    Returns:
        Resultado do comando executado
    """
    try:
        resultado = subprocess.run(
            comando,
            cwd=diretorio,
            capture_output=True,
            text=True,
            check=verificar,
            encoding='utf-8',
            errors='replace'
        )
        return resultado
    except subprocess.CalledProcessError as e:
        imprimir_erro(f"Erro ao executar comando: {' '.join(comando)}")
        imprimir_erro(f"Código de saída: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        raise
    except FileNotFoundError as e:
        # Comando não encontrado (ex: git, dotnet não instalado)
        imprimir_erro(f"Comando não encontrado: {comando[0]}. Certifique-se de que está instalado e no PATH.")
        raise

