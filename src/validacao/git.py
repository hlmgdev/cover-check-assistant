"""Validação de repositório Git."""

import re
from typing import Optional, Dict, Set
from pathlib import Path
from collections import defaultdict

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
            diretorio=caminho,
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
        executar_comando(['git', 'fetch', '--all'], diretorio=caminho_repositorio, verificar=False)
        
        # Lista de branches comuns para tentar
        candidatas = ['origin/main', 'origin/master', 'main', 'master']
        
        for branch in candidatas:
            resultado = executar_comando(
                ['git', 'rev-parse', '--verify', branch],
                diretorio=caminho_repositorio,
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
            diretorio=caminho_repositorio,
            verificar=False
        )
        if resultado.returncode == 0:
            return resultado.stdout.strip()
        return None
    except Exception:
        return None


def obter_arquivos_e_linhas_modificadas(
    caminho_repositorio: Path,
    branch_base: str
) -> Dict[str, Set[int]]:
    """
    Obtém arquivos modificados e os números de linhas alteradas/adicionadas.
    Calcula o diff entre a branch base e HEAD.
    
    Args:
        caminho_repositorio: Caminho do repositório Git
        branch_base: Branch base para comparação (ex: 'origin/main', 'main')
    
    Returns:
        Dicionário {caminho_arquivo: set(números_de_linhas)}
        Exemplo: {'src/MyClass.cs': {10, 11, 12, 25}, 'src/Other.cs': {5, 6}}
    """
    imprimir_info(f"Calculando diff entre HEAD e {branch_base}...")
    
    try:
        # Executa git diff com --unified=0 para obter apenas as linhas modificadas
        resultado = executar_comando(
            ['git', 'diff', branch_base, 'HEAD', '--unified=0'],
            diretorio=caminho_repositorio,
            verificar=True
        )
        
        linhas_modificadas = defaultdict(set)
        arquivo_atual = None
        
        # Parse do output do git diff
        for linha in resultado.stdout.split('\n'):
            # Detecta o início de um novo arquivo
            # Formato: +++ b/caminho/do/arquivo.cs
            if linha.startswith('+++'):
                caminho_arquivo = linha[6:].strip()  # Remove '+++ b/'
                if caminho_arquivo and caminho_arquivo != '/dev/null':
                    arquivo_atual = caminho_arquivo
            
            # Detecta as linhas modificadas
            # Formato: @@ -old_start,old_count +new_start,new_count @@
            elif linha.startswith('@@') and arquivo_atual:
                # Extrai a parte +new_start,new_count
                match = re.search(r'\+(\d+)(?:,(\d+))?', linha)
                if match:
                    linha_inicial = int(match.group(1))
                    # Se não houver count, assume 1 linha
                    quantidade = int(match.group(2)) if match.group(2) else 1
                    
                    # Adiciona todas as linhas do intervalo ao conjunto
                    for num_linha in range(linha_inicial, linha_inicial + quantidade):
                        linhas_modificadas[arquivo_atual].add(num_linha)
        
        # Converte defaultdict para dict normal
        resultado_dict = dict(linhas_modificadas)
        
        # Exibe resumo
        total_arquivos = len(resultado_dict)
        total_linhas = sum(len(linhas) for linhas in resultado_dict.values())
        
        imprimir_sucesso(f"Encontrados {total_arquivos} arquivos modificados com {total_linhas} linhas alteradas")
        
        # Mostra os primeiros 5 arquivos como preview
        for i, (arquivo, linhas) in enumerate(list(resultado_dict.items())[:5]):
            imprimir_info(f"  • {arquivo}: {len(linhas)} linhas modificadas")
        
        if total_arquivos > 5:
            imprimir_info(f"  ... e mais {total_arquivos - 5} arquivos")
        
        return resultado_dict
    
    except Exception as e:
        imprimir_erro(f"Erro ao calcular diff: {e}")
        return {}

