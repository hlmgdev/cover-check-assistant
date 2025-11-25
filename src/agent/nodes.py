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
    instalar_reportgenerator
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
    
    # Atualiza histórico com informações de projetos .NET
    historico[-1].update({
        "total_csproj": len(arquivos_csproj),
        "total_projetos_teste": len(projetos_teste),
        "dotnet_instalado": dotnet_instalado,
        "total_sdks": len(sdks_instalados),
        "sdks_ok": sdks_ok,
        "reportgenerator_instalado": reportgenerator_instalado
    })
    
    print(f"\n✅ Validação do ambiente concluída")
    print(f"   Projetos .NET: {len(arquivos_csproj)}")
    print(f"   Projetos de teste: {len(projetos_teste)}")
    print(f"   SDKs instalados: {len(sdks_instalados)}")
    print(f"   SDKs OK: {'Sim' if sdks_ok else 'Não'}")
    print(f"   ReportGenerator: {'Instalado' if reportgenerator_instalado else 'Não instalado'}")
    
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


# Aliases para compatibilidade
analyze_code_node = no_analisar_codigo
generate_tests_node = no_gerar_testes
validate_tests_node = no_validar_testes
check_coverage_node = no_verificar_cobertura
