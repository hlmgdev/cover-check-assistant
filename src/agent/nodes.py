"""Nós do grafo LangGraph."""

from typing import Dict, Any
from pathlib import Path
from src.agent.state import EstadoAgente
from src.test_generator.generator import GeradorTestes
from src.agent.tools import analisar_estrutura_codigo, validar_codigo_teste
from src.validacao.git import (
    verificar_repositorio_git, 
    detectar_branch_base, 
    obter_branch_atual,
    obter_arquivos_e_linhas_modificadas
)
from src.validacao.dotnet import (
    encontrar_arquivos_csproj,
    identificar_projetos_teste,
    verificar_dotnet_instalado,
    listar_sdks_instalados,
    verificar_sdks_necessarios,
    obter_target_framework,
    verificar_reportgenerator_instalado,
    instalar_reportgenerator,
    verificar_coverlet_projetos,
    instalar_coverlet_projeto
)
from src.validacao.cobertura import (
    executar_testes_com_cobertura,
    mesclar_arquivos_cobertura,
    gerar_relatorio_html,
    filtrar_cobertura_por_diff,
    extrair_resumo_cobertura
)
from src.validacao.utilidades import imprimir_cabecalho


def no_validar_ambiente(estado: EstadoAgente) -> Dict[str, Any]:
    """
    Nó: Valida o ambiente (primeira etapa - sem LLM).
    Valida repositório Git, SDKs, ReportGenerator, Coverlet, etc.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Atualizações para o estado
    """
    imprimir_cabecalho("ETAPA 1: VALIDAÇÃO DO AMBIENTE")
    
    caminho_projeto = estado.get("caminho_projeto")
    if not caminho_projeto:
        return {
            "erros": estado.get("erros", []) + ["Caminho do projeto não fornecido"],
            "validacoes_concluidas": False
        }
    
    caminho_projeto_path = Path(caminho_projeto)
    
    # 1. Validação do repositório Git
    print("\n📋 Validando repositório Git...")
    eh_repositorio = verificar_repositorio_git(caminho_projeto_path)
    
    if not eh_repositorio:
        return {
            "eh_repositorio_git": False,
            "erros": estado.get("erros", []) + ["O caminho fornecido não é um repositório Git válido"],
            "validacoes_concluidas": False
        }
    
    # 2. Detecta branch base e atual
    branch_base = detectar_branch_base(caminho_projeto_path)
    branch_atual = obter_branch_atual(caminho_projeto_path)
    
    print(f"✅ Repositório Git validado")
    if branch_base:
        print(f"   Branch base: {branch_base}")
    if branch_atual:
        print(f"   Branch atual: {branch_atual}")
    
    # 3. Calcula diff Git (arquivos e linhas modificadas)
    arquivos_modificados = {}
    arquivos_cs_modificados = []
    total_linhas_modificadas = 0
    
    if branch_base:
        print("\n📊 Calculando diff Git...")
        arquivos_modificados = obter_arquivos_e_linhas_modificadas(
            caminho_projeto_path,
            branch_base
        )
        
        # Filtra apenas arquivos C# (.cs)
        arquivos_cs_modificados = [
            arquivo for arquivo in arquivos_modificados.keys()
            if arquivo.endswith('.cs')
        ]
        
        total_linhas_modificadas = sum(len(linhas) for linhas in arquivos_modificados.values())
        
        if arquivos_cs_modificados:
            print(f"\n📝 Arquivos C# modificados: {len(arquivos_cs_modificados)}")
            for arquivo in arquivos_cs_modificados[:5]:
                linhas = arquivos_modificados.get(arquivo, set())
                print(f"   • {arquivo}: {len(linhas)} linhas")
            if len(arquivos_cs_modificados) > 5:
                print(f"   ... e mais {len(arquivos_cs_modificados) - 5} arquivos")
        else:
            print("⚠️  Nenhum arquivo C# modificado detectado no diff")
    
    historico = estado.get("historico", [])
    historico.append({
        "acao": "validar_ambiente",
        "repositorio_git": True,
        "branch_base": branch_base,
        "branch_atual": branch_atual,
        "total_arquivos_modificados": len(arquivos_modificados),
        "total_arquivos_cs_modificados": len(arquivos_cs_modificados),
        "total_linhas_modificadas": total_linhas_modificadas
    })
    
    # 4. Descoberta de projetos .NET
    print("\n📦 Descobrindo projetos .NET...")
    arquivos_csproj = encontrar_arquivos_csproj(caminho_projeto_path)
    
    if not arquivos_csproj:
        return {
            "eh_repositorio_git": True,
            "branch_base": branch_base,
            "branch_atual": branch_atual,
            "arquivos_modificados": arquivos_modificados,
            "arquivos_cs_modificados": arquivos_cs_modificados,
            "total_linhas_modificadas": total_linhas_modificadas,
            "arquivos_csproj": [],
            "erros": estado.get("erros", []) + ["Nenhum arquivo .csproj encontrado no repositório"],
            "historico": historico,
            "validacoes_concluidas": False
        }
    
    # Identifica projetos de teste
    projetos_teste = identificar_projetos_teste(arquivos_csproj)
    
    # 5. Verificação do .NET SDK
    print("\n🔧 Verificando .NET SDK...")
    dotnet_instalado = verificar_dotnet_instalado()
    
    if not dotnet_instalado:
        return {
            "eh_repositorio_git": True,
            "branch_base": branch_base,
            "branch_atual": branch_atual,
            "arquivos_modificados": arquivos_modificados,
            "arquivos_cs_modificados": arquivos_cs_modificados,
            "total_linhas_modificadas": total_linhas_modificadas,
            "arquivos_csproj": [str(p) for p in arquivos_csproj],
            "projetos_teste": [str(p) for p in projetos_teste],
            "dotnet_instalado": False,
            "erros": estado.get("erros", []) + [".NET SDK não está instalado"],
            "historico": historico,
            "validacoes_concluidas": False
        }
    
    # Lista SDKs instalados
    sdks_instalados = listar_sdks_instalados()
    
    # Coleta frameworks necessários
    frameworks_necessarios = set()
    for csproj in arquivos_csproj:
        framework = obter_target_framework(csproj)
        if framework:
            frameworks_necessarios.add(framework)
    
    # Verifica se todos os SDKs necessários estão instalados
    sdks_ok, frameworks_faltando = verificar_sdks_necessarios(arquivos_csproj, sdks_instalados)
    
    if not sdks_ok:
        print(f"\n⚠️  Alguns SDKs necessários não estão instalados:")
        for framework in frameworks_faltando:
            print(f"   • {framework}")
    
    # 6. Verificação do ReportGenerator
    print("\n📊 Verificando ReportGenerator...")
    reportgenerator_instalado = verificar_reportgenerator_instalado()
    
    # Se não estiver instalado, oferece instalação automática
    if not reportgenerator_instalado:
        print("\n⚠️  ReportGenerator não está instalado")
        print("   O ReportGenerator é necessário para gerar relatórios HTML de cobertura")
        
        # Por enquanto, apenas registra que não está instalado
        # A instalação pode ser feita manualmente ou em uma fase posterior
        # Para instalar automaticamente, descomente a linha abaixo:
        # reportgenerator_instalado = instalar_reportgenerator()
    
    # 7. Verificação do Coverlet nos projetos de teste
    print("\n🧪 Verificando Coverlet nos projetos de teste...")
    coverlet_ok, projetos_sem_coverlet, tipos_coverlet = verificar_coverlet_projetos(projetos_teste)
    
    # Se houver projetos sem Coverlet, avisa
    if not coverlet_ok and projetos_sem_coverlet:
        print(f"\n⚠️  {len(projetos_sem_coverlet)} projeto(s) de teste sem Coverlet")
        print("   O Coverlet é necessário para coletar dados de cobertura de código")
        
        # Por enquanto, apenas registra
        # Para instalar automaticamente, descomente as linhas abaixo:
        # for projeto in projetos_sem_coverlet:
        #     instalar_coverlet_projeto(projeto, tipo='collector')
    
    # Atualiza histórico com informações de projetos .NET
    historico[-1].update({
        "total_csproj": len(arquivos_csproj),
        "total_projetos_teste": len(projetos_teste),
        "dotnet_instalado": dotnet_instalado,
        "total_sdks": len(sdks_instalados),
        "sdks_ok": sdks_ok,
        "reportgenerator_instalado": reportgenerator_instalado,
        "coverlet_ok": coverlet_ok,
        "projetos_sem_coverlet": len(projetos_sem_coverlet)
    })
    
    print(f"\n✅ Validação do ambiente concluída")
    print(f"   Projetos .NET: {len(arquivos_csproj)}")
    print(f"   Projetos de teste: {len(projetos_teste)}")
    print(f"   SDKs instalados: {len(sdks_instalados)}")
    print(f"   SDKs OK: {'Sim' if sdks_ok else 'Não'}")
    print(f"   ReportGenerator: {'Instalado' if reportgenerator_instalado else 'Não instalado'}")
    print(f"   Coverlet: {'OK' if coverlet_ok else f'{len(projetos_sem_coverlet)} projeto(s) sem Coverlet'}")
    
    return {
        "eh_repositorio_git": True,
        "branch_base": branch_base,
        "branch_atual": branch_atual,
        "arquivos_modificados": arquivos_modificados,
        "arquivos_cs_modificados": arquivos_cs_modificados,
        "total_linhas_modificadas": total_linhas_modificadas,
        "arquivos_csproj": [str(p) for p in arquivos_csproj],
        "projetos_teste": [str(p) for p in projetos_teste],
        "dotnet_instalado": dotnet_instalado,
        "sdks_instalados": sdks_instalados,
        "frameworks_necessarios": frameworks_necessarios,
        "sdks_ok": sdks_ok,
        "reportgenerator_instalado": reportgenerator_instalado,
        "coverlet_ok": coverlet_ok,
        "tipos_coverlet": tipos_coverlet,
        "historico": historico,
        "validacoes_concluidas": True
    }


def no_analisar_codigo(estado: EstadoAgente) -> Dict[str, Any]:
    """
    Nó: Analisa o código fonte e identifica o que precisa de testes.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Atualizações para o estado
    """
    print("🔍 Analisando estrutura do código...")
    
    codigo_fonte = estado.get("codigo_fonte", "")
    if not codigo_fonte:
        return {
            "erros": estado.get("erros", []) + ["Código fonte não fornecido"]
        }
    
    # Usa a ferramenta para analisar o código
    analise = analisar_estrutura_codigo.invoke({"codigo": codigo_fonte})
    
    # Adiciona ao histórico
    historico = estado.get("historico", [])
    historico.append({
        "acao": "analisar_codigo",
        "resultado": analise
    })
    
    print(f"✅ Encontradas {len(analise.get('classes', []))} classes e {len(analise.get('metodos', []))} métodos")
    
    return {
        "historico": historico
    }


def no_gerar_testes(estado: EstadoAgente) -> Dict[str, Any]:
    """
    Nó: Gera testes unitários usando o LLM.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Atualizações para o estado
    """
    print("🤖 Gerando testes unitários...")
    
    codigo_fonte = estado.get("codigo_fonte", "")
    testes_existentes = estado.get("testes_existentes", "")
    iteracao = estado.get("iteracao", 0)
    
    if not codigo_fonte:
        return {
            "erros": estado.get("erros", []) + ["Código fonte não fornecido para geração de testes"]
        }
    
    try:
        gerador = GeradorTestes()
        teste_gerado = gerador.gerar_teste(
            codigo_fonte=codigo_fonte,
            testes_existentes=testes_existentes,
            iteracao=iteracao
        )
        
        if teste_gerado:
            testes_gerados = estado.get("testes_gerados", [])
            testes_gerados.append(teste_gerado)
            
            historico = estado.get("historico", [])
            historico.append({
                "acao": "gerar_testes",
                "iteracao": iteracao,
                "teste_gerado": True
            })
            
            print("✅ Teste gerado com sucesso")
            
            return {
                "testes_gerados": testes_gerados,
                "historico": historico
            }
        else:
            return {
                "erros": estado.get("erros", []) + ["Falha ao gerar teste"]
            }
    
    except Exception as e:
        mensagem_erro = f"Erro ao gerar testes: {str(e)}"
        print(f"❌ {mensagem_erro}")
        return {
            "erros": estado.get("erros", []) + [mensagem_erro]
        }


def no_validar_testes(estado: EstadoAgente) -> Dict[str, Any]:
    """
    Nó: Valida os testes gerados.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Atualizações para o estado
    """
    print("✔️  Validando testes gerados...")
    
    testes_gerados = estado.get("testes_gerados", [])
    if not testes_gerados:
        return {
            "erros": estado.get("erros", []) + ["Nenhum teste gerado para validar"]
        }
    
    # Valida o último teste gerado
    ultimo_teste = testes_gerados[-1]
    validacao = validar_codigo_teste.invoke({"codigo_teste": ultimo_teste})
    
    historico = estado.get("historico", [])
    historico.append({
        "acao": "validar_testes",
        "eh_valido": validacao.get("eh_valido", False),
        "erros": validacao.get("erros", [])
    })
    
    if validacao.get("eh_valido"):
        print("✅ Testes validados com sucesso")
    else:
        erros = validacao.get("erros", [])
        print(f"⚠️  Testes com problemas: {', '.join(erros)}")
    
    return {
        "historico": historico
    }


def no_verificar_cobertura(estado: EstadoAgente) -> Dict[str, Any]:
    """
    Nó: Verifica a cobertura atual e decide se continua ou termina.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Atualizações para o estado e decisão de continuação
    """
    print("📊 Verificando cobertura...")
    
    cobertura = estado.get("percentual_cobertura", 0.0)
    meta = estado.get("meta_cobertura", 80.0)
    iteracao = estado.get("iteracao", 0)
    max_iteracoes = estado.get("max_iteracoes", 5)
    
    historico = estado.get("historico", [])
    historico.append({
        "acao": "verificar_cobertura",
        "cobertura_atual": cobertura,
        "meta_cobertura": meta,
        "iteracao": iteracao
    })
    
    print(f"📈 Cobertura atual: {cobertura:.1f}% | Meta: {meta:.1f}%")
    
    # Verifica se atingiu a meta ou excedeu iterações
    deve_continuar = cobertura < meta and iteracao < max_iteracoes
    
    if cobertura >= meta:
        print(f"🎉 Meta de cobertura atingida! ({cobertura:.1f}% >= {meta:.1f}%)")
    elif iteracao >= max_iteracoes:
        print(f"⚠️  Número máximo de iterações atingido ({max_iteracoes})")
    
    return {
        "historico": historico,
        "deve_continuar": deve_continuar
    }


def no_executar_cobertura(estado: EstadoAgente) -> Dict[str, Any]:
    """
    Nó: Executa testes com cobertura e gera relatórios.
    
    Args:
        estado: Estado atual do agente
    
    Returns:
        Atualizações para o estado
    """
    imprimir_cabecalho("EXECUÇÃO DE COBERTURA")
    
    caminho_projeto = estado.get("caminho_projeto")
    projetos_teste = estado.get("projetos_teste", [])
    tipos_coverlet = estado.get("tipos_coverlet", {})
    arquivos_modificados = estado.get("arquivos_modificados", {})
    
    if not caminho_projeto:
        return {"erros": estado.get("erros", []) + ["Caminho do projeto não fornecido"]}
    
    if not projetos_teste:
        return {"erros": estado.get("erros", []) + ["Nenhum projeto de teste encontrado"]}
    
    caminho_projeto_path = Path(caminho_projeto)
    diretorio_cobertura = caminho_projeto_path / ".coverage-reports"
    
    # 1. Executa testes com cobertura para cada projeto
    print("\n🧪 Executando testes com cobertura...")
    arquivos_cobertura = []
    
    for projeto_str in projetos_teste:
        projeto = Path(projeto_str)
        tipo_coverlet = tipos_coverlet.get(projeto_str, 'collector')
        
        arquivo_cob = executar_testes_com_cobertura(
            projeto,
            tipo_coverlet,
            diretorio_cobertura
        )
        
        if arquivo_cob:
            arquivos_cobertura.append(arquivo_cob)
    
    if not arquivos_cobertura:
        return {
            "erros": estado.get("erros", []) + ["Nenhum arquivo de cobertura foi gerado"],
            "arquivos_cobertura": []
        }
    
    print(f"\n✅ {len(arquivos_cobertura)} arquivo(s) de cobertura gerado(s)")
    
    # 2. Mescla arquivos de cobertura
    print("\n📊 Mesclando arquivos de cobertura...")
    arquivo_mesclado = diretorio_cobertura / "coverage_merged.cobertura.xml"
    
    if mesclar_arquivos_cobertura(arquivos_cobertura, arquivo_mesclado):
        print(f"✅ Arquivo mesclado: {arquivo_mesclado.name}")
    else:
        arquivo_mesclado = None
    
    # 3. Gera relatório HTML geral
    print("\n📄 Gerando relatório HTML geral...")
    relatorio_geral = diretorio_cobertura / "html-report"
    relatorio_html_ok = False
    
    if arquivo_mesclado and arquivo_mesclado.exists():
        relatorio_html_ok = gerar_relatorio_html(
            arquivo_mesclado,
            relatorio_geral,
            "Relatório de Cobertura Geral"
        )
    
    # 4. Filtra cobertura por diff (se houver arquivos modificados)
    arquivo_diff = None
    relatorio_diff = None
    
    if arquivos_modificados and arquivo_mesclado and arquivo_mesclado.exists():
        print("\n🔍 Filtrando cobertura por diff...")
        arquivo_diff = diretorio_cobertura / "coverage_diff.cobertura.xml"
        
        if filtrar_cobertura_por_diff(arquivo_mesclado, arquivos_modificados, arquivo_diff):
            print(f"✅ Cobertura filtrada: {arquivo_diff.name}")
            
            # 5. Gera relatório HTML do diff
            print("\n📄 Gerando relatório HTML do diff...")
            relatorio_diff = diretorio_cobertura / "html-report-diff"
            
            gerar_relatorio_html(
                arquivo_diff,
                relatorio_diff,
                "Relatório de Cobertura - Diff"
            )
    
    # 6. Extrai resumo de cobertura
    resumo_cobertura = {}
    if arquivo_mesclado and arquivo_mesclado.exists():
        resumo = extrair_resumo_cobertura(arquivo_mesclado)
        if resumo:
            resumo_cobertura = resumo
            print(f"\n📊 Resumo de Cobertura:")
            print(f"   Cobertura de linhas: {resumo['line_coverage']:.2f}%")
            print(f"   Linhas cobertas: {resumo['lines_covered']}/{resumo['lines_valid']}")
    
    # Atualiza histórico
    historico = estado.get("historico", [])
    historico.append({
        "acao": "executar_cobertura",
        "arquivos_gerados": len(arquivos_cobertura),
        "relatorio_html": relatorio_html_ok,
        "cobertura_percentual": resumo_cobertura.get('line_coverage', 0.0)
    })
    
    return {
        "arquivos_cobertura": [str(f) for f in arquivos_cobertura],
        "arquivo_cobertura_mesclado": str(arquivo_mesclado) if arquivo_mesclado else None,
        "arquivo_cobertura_diff": str(arquivo_diff) if arquivo_diff else None,
        "relatorio_html_geral": str(relatorio_geral / "index.html") if relatorio_html_ok else None,
        "relatorio_html_diff": str(relatorio_diff / "index.html") if relatorio_diff and relatorio_diff.exists() else None,
        "resumo_cobertura": resumo_cobertura,
        "percentual_cobertura": resumo_cobertura.get('line_coverage', 0.0),
        "historico": historico
    }


# Aliases para compatibilidade
analyze_code_node = no_analisar_codigo
generate_tests_node = no_gerar_testes
validate_tests_node = no_validar_testes
check_coverage_node = no_verificar_cobertura
run_coverage_node = no_executar_cobertura
