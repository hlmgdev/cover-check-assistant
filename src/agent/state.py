"""Definição do estado do agente."""

from typing import TypedDict, List, Dict, Optional, Any, Set


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
        # Validações da primeira etapa
        eh_repositorio_git: Flag indicando se é repositório Git válido
        branch_base: Branch base para comparação
        branch_atual: Branch atual do repositório
        validacoes_concluidas: Flag indicando se validações foram concluídas
        # Análise de diff Git
        arquivos_modificados: Dicionário mapeando arquivos para linhas modificadas
        total_linhas_modificadas: Total de linhas modificadas no diff
        arquivos_cs_modificados: Lista de arquivos C# (.cs) modificados
        # Descoberta de projetos .NET
        arquivos_csproj: Lista de caminhos para arquivos .csproj encontrados
        projetos_teste: Lista de projetos de teste identificados
        dotnet_instalado: Flag indicando se .NET SDK está instalado
        sdks_instalados: Lista de versões de SDKs instalados
        frameworks_necessarios: Set de frameworks necessários pelos projetos
        sdks_ok: Flag indicando se todos os SDKs necessários estão disponíveis
        reportgenerator_instalado: Flag indicando se ReportGenerator está instalado
        coverlet_ok: Flag indicando se todos os projetos de teste têm Coverlet
        tipos_coverlet: Dict mapeando projetos para tipo de Coverlet (collector/msbuild)
        # Cobertura de código
        arquivos_cobertura: Lista de arquivos de cobertura gerados
        arquivo_cobertura_mesclado: Caminho para arquivo de cobertura mesclado
        arquivo_cobertura_diff: Caminho para arquivo de cobertura filtrado por diff
        relatorio_html_geral: Caminho para relatório HTML geral
        relatorio_html_diff: Caminho para relatório HTML do diff
        resumo_cobertura: Dict com métricas de cobertura
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
    # Validações da primeira etapa
    eh_repositorio_git: bool
    branch_base: Optional[str]
    branch_atual: Optional[str]
    validacoes_concluidas: bool
    # Análise de diff Git
    arquivos_modificados: Dict[str, Set[int]]  # {arquivo: {linhas modificadas}}
    total_linhas_modificadas: int
    arquivos_cs_modificados: List[str]  # Lista de arquivos .cs modificados
    # Descoberta de projetos .NET
    arquivos_csproj: List[str]  # Caminhos para arquivos .csproj (como strings)
    projetos_teste: List[str]  # Caminhos para projetos de teste
    dotnet_instalado: bool
    sdks_instalados: List[str]  # Versões de SDKs instalados
    frameworks_necessarios: Set[str]  # Frameworks necessários (ex: 'net8.0')
    sdks_ok: bool  # Todos os SDKs necessários estão instalados
    reportgenerator_instalado: bool  # ReportGenerator está instalado
    coverlet_ok: bool  # Todos os projetos de teste têm Coverlet
    tipos_coverlet: Dict[str, str]  # {projeto: tipo_coverlet}
    # Cobertura de código
    arquivos_cobertura: List[str]  # Arquivos de cobertura gerados
    arquivo_cobertura_mesclado: Optional[str]  # Arquivo mesclado
    arquivo_cobertura_diff: Optional[str]  # Arquivo filtrado por diff
    relatorio_html_geral: Optional[str]  # Relatório HTML geral
    relatorio_html_diff: Optional[str]  # Relatório HTML do diff
    resumo_cobertura: Dict[str, Any]  # Métricas de cobertura

# Alias para compatibilidade
AgentState = EstadoAgente
