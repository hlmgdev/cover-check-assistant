"""Gerenciamento de cobertura de código .NET."""

import json
import shutil
from typing import List, Optional, Dict, Set, Tuple
from pathlib import Path

from .utilidades import (
    executar_comando,
    imprimir_info,
    imprimir_sucesso,
    imprimir_erro,
    imprimir_aviso
)


def executar_testes_com_cobertura(
    caminho_projeto_teste: Path,
    tipo_coverlet: str,
    diretorio_saida: Path
) -> Optional[Path]:
    """
    Executa testes com cobertura usando Coverlet.
    
    Args:
        caminho_projeto_teste: Caminho para o arquivo .csproj de teste
        tipo_coverlet: Tipo de Coverlet ('collector' ou 'msbuild')
        diretorio_saida: Diretório para salvar arquivos de cobertura
    
    Returns:
        Caminho para o arquivo de cobertura gerado ou None em caso de erro
    """
    imprimir_info(f"Executando testes com cobertura: {caminho_projeto_teste.name}")
    
    # Cria diretório de saída se não existir
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    
    # Nome do arquivo de cobertura
    nome_arquivo = f"{caminho_projeto_teste.stem}_coverage.cobertura.xml"
    arquivo_cobertura = diretorio_saida / nome_arquivo
    
    try:
        # Primeiro, faz build do projeto
        imprimir_info("Compilando projeto de teste...")
        build_resultado = executar_comando(
            ['dotnet', 'build', str(caminho_projeto_teste)],
            diretorio=caminho_projeto_teste.parent,
            verificar=False
        )
        
        if build_resultado.returncode != 0:
            imprimir_erro("Falha ao compilar projeto de teste")
            return None
        
        if tipo_coverlet == 'collector':
            # Usa coverlet.collector (via runsettings)
            comando = [
                'dotnet', 'test',
                str(caminho_projeto_teste),
                '--collect:"XPlat Code Coverage"',
                '--results-directory', str(diretorio_saida),
                '--no-build',  # Já fizemos build acima
                '--',
                'DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=cobertura'
            ]
        else:
            # Usa coverlet.msbuild
            comando = [
                'dotnet', 'test',
                str(caminho_projeto_teste),
                '/p:CollectCoverage=true',
                f'/p:CoverletOutputFormat=cobertura',
                f'/p:CoverletOutput={arquivo_cobertura}',
                '--no-build'  # Já fizemos build acima
            ]
        
        resultado = executar_comando(
            comando,
            diretorio=caminho_projeto_teste.parent,
            verificar=False
        )
        
        if resultado.returncode == 0:
            # Para collector, precisa encontrar o arquivo gerado
            if tipo_coverlet == 'collector':
                # Procura por arquivos coverage.cobertura.xml no diretório de saída
                arquivos_encontrados = list(diretorio_saida.rglob('coverage.cobertura.xml'))
                if arquivos_encontrados:
                    # Move para nome padronizado
                    shutil.move(str(arquivos_encontrados[0]), str(arquivo_cobertura))
                    imprimir_sucesso(f"Cobertura gerada: {arquivo_cobertura.name}")
                    return arquivo_cobertura
                else:
                    imprimir_aviso("Arquivo de cobertura não encontrado")
                    return None
            else:
                if arquivo_cobertura.exists():
                    imprimir_sucesso(f"Cobertura gerada: {arquivo_cobertura.name}")
                    return arquivo_cobertura
                else:
                    imprimir_aviso("Arquivo de cobertura não foi criado")
                    return None
        else:
            imprimir_erro(f"Falha ao executar testes: código {resultado.returncode}")
            if resultado.stderr:
                imprimir_erro(f"Erro: {resultado.stderr[:500]}")
            return None
    
    except Exception as e:
        imprimir_erro(f"Erro ao executar testes com cobertura: {e}")
        return None


def mesclar_arquivos_cobertura(
    arquivos_cobertura: List[Path],
    arquivo_saida: Path
) -> bool:
    """
    Mescla múltiplos arquivos de cobertura em um único arquivo.
    
    Args:
        arquivos_cobertura: Lista de arquivos de cobertura para mesclar
        arquivo_saida: Caminho para o arquivo de saída mesclado
    
    Returns:
        True se mesclagem foi bem-sucedida, False caso contrário
    """
    if not arquivos_cobertura:
        imprimir_aviso("Nenhum arquivo de cobertura para mesclar")
        return False
    
    if len(arquivos_cobertura) == 1:
        # Apenas um arquivo, copia para saída
        imprimir_info("Apenas um arquivo de cobertura, copiando...")
        shutil.copy(str(arquivos_cobertura[0]), str(arquivo_saida))
        imprimir_sucesso(f"Arquivo copiado: {arquivo_saida.name}")
        return True
    
    imprimir_info(f"Mesclando {len(arquivos_cobertura)} arquivos de cobertura...")
    
    try:
        # Usa ReportGenerator para mesclar
        comando = [
            'reportgenerator',
            f'-reports:{";".join(str(f) for f in arquivos_cobertura)}',
            f'-targetdir:{arquivo_saida.parent}',
            '-reporttypes:Cobertura',
            f'-assemblyfilters:+*'
        ]
        
        resultado = executar_comando(comando, verificar=False)
        
        if resultado.returncode == 0:
            # ReportGenerator cria Cobertura.xml
            arquivo_gerado = arquivo_saida.parent / 'Cobertura.xml'
            if arquivo_gerado.exists():
                # Renomeia para o nome desejado
                shutil.move(str(arquivo_gerado), str(arquivo_saida))
                imprimir_sucesso(f"Arquivos mesclados: {arquivo_saida.name}")
                return True
            else:
                imprimir_erro("Arquivo mesclado não foi criado")
                return False
        else:
            imprimir_erro("Falha ao mesclar arquivos de cobertura")
            return False
    
    except Exception as e:
        imprimir_erro(f"Erro ao mesclar arquivos: {e}")
        return False


def gerar_relatorio_html(
    arquivo_cobertura: Path,
    diretorio_saida: Path,
    titulo: str = "Relatório de Cobertura"
) -> bool:
    """
    Gera relatório HTML de cobertura usando ReportGenerator.
    
    Args:
        arquivo_cobertura: Arquivo de cobertura (formato Cobertura XML)
        diretorio_saida: Diretório para salvar o relatório HTML
        titulo: Título do relatório
    
    Returns:
        True se geração foi bem-sucedida, False caso contrário
    """
    imprimir_info(f"Gerando relatório HTML: {titulo}")
    
    if not arquivo_cobertura.exists():
        imprimir_erro(f"Arquivo de cobertura não encontrado: {arquivo_cobertura}")
        return False
    
    # Cria diretório de saída
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    
    try:
        comando = [
            'reportgenerator',
            f'-reports:{arquivo_cobertura}',
            f'-targetdir:{diretorio_saida}',
            '-reporttypes:Html',
            f'-title:{titulo}'
        ]
        
        resultado = executar_comando(comando, verificar=False)
        
        if resultado.returncode == 0:
            arquivo_index = diretorio_saida / 'index.html'
            if arquivo_index.exists():
                imprimir_sucesso(f"Relatório HTML gerado: {arquivo_index}")
                return True
            else:
                imprimir_erro("Arquivo index.html não foi criado")
                return False
        else:
            imprimir_erro("Falha ao gerar relatório HTML")
            if resultado.stderr:
                imprimir_erro(f"Erro: {resultado.stderr[:500]}")
            return False
    
    except Exception as e:
        imprimir_erro(f"Erro ao gerar relatório HTML: {e}")
        return False


def filtrar_cobertura_por_diff(
    arquivo_cobertura: Path,
    arquivos_modificados: Dict[str, Set[int]],
    arquivo_saida: Path
) -> bool:
    """
    Filtra arquivo de cobertura para incluir apenas linhas modificadas.
    
    Args:
        arquivo_cobertura: Arquivo de cobertura original
        arquivos_modificados: Dict {arquivo: {linhas modificadas}}
        arquivo_saida: Arquivo de saída filtrado
    
    Returns:
        True se filtragem foi bem-sucedida, False caso contrário
    """
    imprimir_info("Filtrando cobertura por diff...")
    
    if not arquivo_cobertura.exists():
        imprimir_erro(f"Arquivo de cobertura não encontrado: {arquivo_cobertura}")
        return False
    
    if not arquivos_modificados:
        imprimir_aviso("Nenhum arquivo modificado para filtrar")
        return False
    
    try:
        import xml.etree.ElementTree as ET
        
        # Parse do arquivo de cobertura
        tree = ET.parse(arquivo_cobertura)
        root = tree.getroot()
        
        # Normaliza caminhos dos arquivos modificados (usa apenas nome do arquivo)
        arquivos_mod_normalizados = {}
        for caminho, linhas in arquivos_modificados.items():
            # Converte para Path e pega apenas o nome do arquivo
            nome_arquivo = Path(caminho).name
            arquivos_mod_normalizados[nome_arquivo] = linhas
        
        linhas_filtradas = 0
        linhas_totais = 0
        
        # Itera sobre as classes no XML de cobertura
        for package in root.findall('.//package'):
            for classe in package.findall('classes/class'):
                filename = classe.get('filename', '')
                nome_arquivo = Path(filename).name
                
                # Verifica se este arquivo foi modificado
                if nome_arquivo in arquivos_mod_normalizados:
                    linhas_modificadas = arquivos_mod_normalizados[nome_arquivo]
                    
                    # Filtra linhas
                    for linha in classe.findall('lines/line'):
                        numero_linha = int(linha.get('number', 0))
                        linhas_totais += 1
                        
                        # Remove linhas que não foram modificadas
                        if numero_linha not in linhas_modificadas:
                            classe.find('lines').remove(linha)
                        else:
                            linhas_filtradas += 1
                else:
                    # Remove classe inteira se arquivo não foi modificado
                    package.find('classes').remove(classe)
        
        # Salva arquivo filtrado
        tree.write(str(arquivo_saida), encoding='utf-8', xml_declaration=True)
        
        imprimir_sucesso(f"Cobertura filtrada: {linhas_filtradas} de {linhas_totais} linhas mantidas")
        imprimir_info(f"Arquivo salvo: {arquivo_saida}")
        
        return True
    
    except Exception as e:
        imprimir_erro(f"Erro ao filtrar cobertura: {e}")
        return False


def extrair_resumo_cobertura(arquivo_cobertura: Path) -> Optional[Dict[str, float]]:
    """
    Extrai resumo de cobertura do arquivo XML.
    
    Args:
        arquivo_cobertura: Arquivo de cobertura (formato Cobertura XML)
    
    Returns:
        Dict com métricas de cobertura ou None em caso de erro
    """
    if not arquivo_cobertura.exists():
        imprimir_erro(f"Arquivo de cobertura não encontrado: {arquivo_cobertura}")
        return None
    
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(arquivo_cobertura)
        root = tree.getroot()
        
        # Extrai métricas do elemento raiz
        line_rate = float(root.get('line-rate', 0.0))
        branch_rate = float(root.get('branch-rate', 0.0))
        
        # Conta linhas
        lines_covered = int(root.get('lines-covered', 0))
        lines_valid = int(root.get('lines-valid', 0))
        
        resumo = {
            'line_coverage': line_rate * 100,  # Converte para percentual
            'branch_coverage': branch_rate * 100,
            'lines_covered': lines_covered,
            'lines_valid': lines_valid,
            'lines_uncovered': lines_valid - lines_covered
        }
        
        return resumo
    
    except Exception as e:
        imprimir_erro(f"Erro ao extrair resumo de cobertura: {e}")
        return None
