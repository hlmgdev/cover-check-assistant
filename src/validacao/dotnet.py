"""Validação e descoberta de projetos .NET."""

import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple
from pathlib import Path

from .utilidades import (
    executar_comando,
    imprimir_info,
    imprimir_sucesso,
    imprimir_erro,
    imprimir_aviso
)


def encontrar_arquivos_csproj(caminho_repositorio: Path) -> List[Path]:
    """
    Encontra todos os arquivos .csproj no repositório.
    
    Args:
        caminho_repositorio: Caminho do repositório
    
    Returns:
        Lista de caminhos para arquivos .csproj encontrados
    """
    imprimir_info("Procurando arquivos .csproj...")
    
    try:
        arquivos_csproj = list(caminho_repositorio.rglob('*.csproj'))
        
        if arquivos_csproj:
            imprimir_sucesso(f"Encontrados {len(arquivos_csproj)} arquivos .csproj")
            for arquivo in arquivos_csproj:
                # Mostra caminho relativo ao repositório
                caminho_relativo = arquivo.relative_to(caminho_repositorio)
                imprimir_info(f"  • {caminho_relativo}")
        else:
            imprimir_aviso("Nenhum arquivo .csproj encontrado no repositório")
        
        return arquivos_csproj
    
    except Exception as e:
        imprimir_erro(f"Erro ao procurar arquivos .csproj: {e}")
        return []


def obter_target_framework(caminho_csproj: Path) -> Optional[str]:
    """
    Obtém o TargetFramework de um arquivo .csproj.
    
    Args:
        caminho_csproj: Caminho para o arquivo .csproj
    
    Returns:
        String do TargetFramework (ex: 'net8.0', 'net6.0') ou None se não encontrado
    """
    try:
        tree = ET.parse(caminho_csproj)
        root = tree.getroot()
        
        # Procura por TargetFramework
        for elem in root.iter('TargetFramework'):
            return elem.text
        
        # Procura por TargetFrameworks (múltiplos)
        for elem in root.iter('TargetFrameworks'):
            frameworks = elem.text.split(';')
            return frameworks[0] if frameworks else None
        
        return None
    
    except Exception as e:
        imprimir_aviso(f"Erro ao ler {caminho_csproj.name}: {e}")
        return None


def eh_projeto_teste(caminho_csproj: Path) -> bool:
    """
    Verifica se um projeto é um projeto de teste.
    
    Args:
        caminho_csproj: Caminho para o arquivo .csproj
    
    Returns:
        True se for projeto de teste, False caso contrário
    """
    try:
        # Verifica o nome do projeto
        if 'test' in caminho_csproj.name.lower():
            return True
        
        # Verifica referências a frameworks de teste no XML
        tree = ET.parse(caminho_csproj)
        root = tree.getroot()
        
        test_packages = ['xunit', 'nunit', 'mstest', 'Microsoft.NET.Test.Sdk']
        for elem in root.iter('PackageReference'):
            include = elem.get('Include', '')
            if any(pkg.lower() in include.lower() for pkg in test_packages):
                return True
        
        return False
    
    except Exception as e:
        imprimir_aviso(f"Erro ao verificar projeto de teste {caminho_csproj.name}: {e}")
        return False


def identificar_projetos_teste(arquivos_csproj: List[Path]) -> List[Path]:
    """
    Identifica quais projetos são projetos de teste.
    
    Args:
        arquivos_csproj: Lista de arquivos .csproj
    
    Returns:
        Lista de projetos de teste
    """
    imprimir_info("Identificando projetos de teste...")
    
    projetos_teste = [proj for proj in arquivos_csproj if eh_projeto_teste(proj)]
    
    if projetos_teste:
        imprimir_sucesso(f"Encontrados {len(projetos_teste)} projetos de teste")
        for proj in projetos_teste:
            imprimir_info(f"  • {proj.name}")
    else:
        imprimir_aviso("Nenhum projeto de teste encontrado")
    
    return projetos_teste


def verificar_dotnet_instalado() -> bool:
    """
    Verifica se o comando dotnet está disponível.
    
    Returns:
        True se dotnet está instalado, False caso contrário
    """
    imprimir_info("Verificando instalação do .NET SDK...")
    
    try:
        resultado = executar_comando(['dotnet', '--version'], verificar=False)
        
        if resultado.returncode == 0:
            versao = resultado.stdout.strip()
            imprimir_sucesso(f".NET SDK instalado: versão {versao}")
            return True
        else:
            imprimir_erro(".NET SDK não encontrado")
            return False
    
    except FileNotFoundError:
        imprimir_erro(".NET SDK não está instalado ou não está no PATH")
        return False
    except Exception as e:
        imprimir_erro(f"Erro ao verificar .NET SDK: {e}")
        return False


def listar_sdks_instalados() -> List[str]:
    """
    Lista os SDKs do .NET instalados.
    
    Returns:
        Lista de versões de SDKs instalados
    """
    imprimir_info("Listando SDKs do .NET instalados...")
    
    try:
        resultado = executar_comando(['dotnet', '--list-sdks'], verificar=False)
        
        if resultado.returncode != 0:
            imprimir_erro("Falha ao listar SDKs")
            return []
        
        sdks = []
        for linha in resultado.stdout.split('\n'):
            if linha.strip():
                # Formato: "8.0.100 [C:\Program Files\dotnet\sdk]"
                versao = linha.split()[0]
                sdks.append(versao)
        
        if sdks:
            imprimir_sucesso(f"Encontrados {len(sdks)} SDKs instalados:")
            for sdk in sdks:
                imprimir_info(f"  • {sdk}")
        else:
            imprimir_aviso("Nenhum SDK encontrado")
        
        return sdks
    
    except Exception as e:
        imprimir_erro(f"Erro ao listar SDKs: {e}")
        return []


def verificar_sdks_necessarios(
    arquivos_csproj: List[Path],
    sdks_instalados: List[str]
) -> Tuple[bool, List[str]]:
    """
    Verifica se todos os SDKs necessários estão instalados.
    
    Args:
        arquivos_csproj: Lista de arquivos .csproj
        sdks_instalados: Lista de SDKs instalados
    
    Returns:
        Tupla (todos_ok, frameworks_faltando)
    """
    imprimir_info("Verificando SDKs necessários...")
    
    # Coleta todos os frameworks necessários
    frameworks_necessarios = set()
    for csproj in arquivos_csproj:
        framework = obter_target_framework(csproj)
        if framework:
            frameworks_necessarios.add(framework)
    
    if not frameworks_necessarios:
        imprimir_aviso("Nenhum framework foi detectado nos arquivos .csproj")
        return True, []
    
    imprimir_info(f"Frameworks necessários: {', '.join(frameworks_necessarios)}")
    
    # Extrai versões major dos SDKs instalados
    sdks_majors = set()
    for sdk in sdks_instalados:
        try:
            major = int(sdk.split('.')[0])
            sdks_majors.add(major)
        except (ValueError, IndexError):
            continue
    
    imprimir_info(f"SDKs instalados (versões major): {sorted(sdks_majors)}")
    
    # Verifica cada framework necessário
    frameworks_faltando = []
    for framework in frameworks_necessarios:
        # Extrai versão major do framework (ex: net8.0 -> 8)
        match = re.search(r'net(\d+)', framework.lower())
        if match:
            framework_major = int(match.group(1))
            
            # Para frameworks antigos (< 5), qualquer SDK >= 5 serve
            if framework_major < 5:
                if any(m >= 5 for m in sdks_majors):
                    imprimir_info(f"  ✓ {framework}: SDK moderno disponível")
                    continue
            
            # Para frameworks modernos, verifica se existe SDK compatível
            if framework_major in sdks_majors:
                imprimir_info(f"  ✓ {framework}: SDK {framework_major}.x encontrado")
            else:
                imprimir_aviso(f"  ✗ {framework}: SDK {framework_major}.x não encontrado")
                frameworks_faltando.append(framework)
    
    if frameworks_faltando:
        imprimir_aviso(f"Frameworks sem SDK correspondente: {', '.join(frameworks_faltando)}")
        return False, frameworks_faltando
    else:
        imprimir_sucesso("Todos os SDKs necessários estão instalados")
        return True, []
