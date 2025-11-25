"""Validação de repositório Git."""

from typing import Optional
from pathlib import Path

from .utilidades import executar_comando, imprimir_info, imprimir_sucesso, imprimir_erro, imprimir_aviso


def verificar_repositorio_git(caminho: Path) -> bool:
    """
    Verifica se o caminho é um repositório Git válido.
    
    Args:
        caminho: Caminho para verificar
    
    Returns:
        True se for um repositório Git válido, False caso contrário
    """
    imprimir_info(f"Verificando se '{caminho}' é um repositório Git...")
    
    try:
        resultado = executar_comando(
            ['git', 'rev-parse', '--git-dir'],
            cwd=caminho,
            verificar=False
        )
        eh_repositorio = resultado.returncode == 0
        
        if eh_repositorio:
            imprimir_sucesso("Repositório Git válido detectado")
        else:
            imprimir_erro("Não é um repositório Git válido")
        
        return eh_repositorio
    except FileNotFoundError:
        imprimir_erro("Git não está instalado ou não está no PATH")
        return False
    except Exception as e:
        imprimir_erro(f"Erro ao verificar repositório Git: {e}")
        return False


def detectar_branch_base(caminho_repositorio: Path) -> Optional[str]:
    """
    Detecta automaticamente uma branch base adequada.
    
    Args:
        caminho_repositorio: Caminho do repositório Git
    
    Returns:
        Nome da branch base detectada ou None se não encontrada
    """
    imprimir_info("Detectando branch base...")
    
    try:
        # Atualiza as refs remotas
        executar_comando(['git', 'fetch', '--all'], cwd=caminho_repositorio, verificar=False)
        
        # Lista de branches comuns para tentar
        candidatas = ['origin/main', 'origin/master', 'main', 'master']
        
        for branch in candidatas:
            resultado = executar_comando(
                ['git', 'rev-parse', '--verify', branch],
                cwd=caminho_repositorio,
                verificar=False
            )
            if resultado.returncode == 0:
                imprimir_sucesso(f"Branch base detectada: {branch}")
                return branch
        
        imprimir_aviso("Nenhuma branch base padrão encontrada")
        return None
    except Exception as e:
        imprimir_erro(f"Erro ao detectar branch base: {e}")
        return None


def obter_branch_atual(caminho_repositorio: Path) -> Optional[str]:
    """
    Obtém o nome da branch atual.
    
    Args:
        caminho_repositorio: Caminho do repositório Git
    
    Returns:
        Nome da branch atual ou None em caso de erro
    """
    try:
        resultado = executar_comando(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=caminho_repositorio,
            verificar=False
        )
        if resultado.returncode == 0:
            return resultado.stdout.strip()
        return None
    except Exception:
        return None

