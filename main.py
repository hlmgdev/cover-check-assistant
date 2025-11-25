#!/usr/bin/env python3
"""
Ponto de entrada principal do agente de geração de testes unitários.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configura encoding UTF-8 para o console (Windows)
if sys.platform == 'win32':
    try:
        # Tenta configurar o console para UTF-8
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        # Se falhar, continua sem encoding especial
        pass

from src.agent.graph import criar_grafo_agente
from src.agent.state import EstadoAgente


def carregar_configuracao():
    """Carrega configurações do arquivo .env."""
    arquivo_env = Path(".env")
    if not arquivo_env.exists():
        print("⚠️  Arquivo .env não encontrado. Usando variáveis de ambiente do sistema.")
        print("   Para configurar, copie .env.example para .env e edite com suas chaves.")
    else:
        load_dotenv(arquivo_env)
        print("✅ Configurações carregadas do arquivo .env")


def criar_estado_inicial(
    codigo_fonte: str,
    caminho_arquivo: str = None,
    caminho_projeto: str = None
) -> EstadoAgente:
    """
    Cria o estado inicial do agente.
    
    Args:
        codigo_fonte: Código fonte C# a ser testado
        caminho_arquivo: Caminho do arquivo (opcional)
        caminho_projeto: Caminho do projeto (opcional)
    
    Returns:
        Estado inicial do agente
    """
    meta_cobertura = float(os.getenv("TARGET_COVERAGE_PERCENTAGE", "80"))
    max_iteracoes = int(os.getenv("MAX_ITERATIONS", "5"))
    
    return {
        "codigo_fonte": codigo_fonte,
        "testes_existentes": "",
        "testes_gerados": [],
        "percentual_cobertura": 0.0,
        "meta_cobertura": meta_cobertura,
        "iteracao": 0,
        "max_iteracoes": max_iteracoes,
        "historico": [],
        "erros": [],
        "caminho_arquivo": caminho_arquivo,
        "caminho_projeto": caminho_projeto,
        "deve_continuar": False,
        # Validações da primeira etapa
        "eh_repositorio_git": False,
        "branch_base": None,
        "branch_atual": None,
        "validacoes_concluidas": False,
        # Análise de diff Git
        "arquivos_modificados": {},
        "total_linhas_modificadas": 0,
        "arquivos_cs_modificados": [],
        # Descoberta de projetos .NET
        "arquivos_csproj": [],
        "projetos_teste": [],
        "dotnet_instalado": False,
        "sdks_instalados": [],
        "frameworks_necessarios": set(),
        "sdks_ok": False,
        "reportgenerator_instalado": False
    }


def main():
    """Função principal."""
    print("=" * 80)
    print("🤖 AGENTE DE GERAÇÃO DE TESTES UNITÁRIOS")
    print("=" * 80)
    print()
    
    # Carrega configurações
    carregar_configuracao()
    print()
    
    # Verifica se foi fornecido código fonte
    if len(sys.argv) < 2:
        print("❌ Uso: python main.py <caminho_do_arquivo.cs> [caminho_do_projeto]")
        print()
        print("Exemplo:")
        print("  python main.py src/MyClass.cs")
        print("  python main.py src/MyClass.cs /path/to/project")
        sys.exit(1)
    
    caminho_arquivo = Path(sys.argv[1])
    if not caminho_arquivo.exists():
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        sys.exit(1)
    
    caminho_projeto = None
    if len(sys.argv) >= 3:
        caminho_projeto = Path(sys.argv[2])
        if not caminho_projeto.exists():
            print(f"⚠️  Caminho do projeto não encontrado: {caminho_projeto}")
            caminho_projeto = None
    else:
        # Se não fornecido, usa o diretório pai do arquivo como projeto
        caminho_projeto = caminho_arquivo.parent
    
    # Lê o código fonte
    print(f"📖 Lendo arquivo: {caminho_arquivo}")
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            codigo_fonte = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        sys.exit(1)
    
    print(f"✅ Arquivo lido ({len(codigo_fonte)} caracteres)")
    print()
    
    # Cria o estado inicial
    estado_inicial = criar_estado_inicial(
        codigo_fonte=codigo_fonte,
        caminho_arquivo=str(caminho_arquivo),
        caminho_projeto=str(caminho_projeto) if caminho_projeto else None
    )
    
    # Cria e executa o grafo do agente
    print("🚀 Iniciando agente...")
    print()
    
    try:
        app = criar_grafo_agente()
        
        # Executa o agente
        config = {"configurable": {"thread_id": "1"}}
        estado_final = None
        
        for estado in app.stream(estado_inicial, config):
            # Processa cada estado retornado
            for nome_no, estado_no in estado.items():
                if nome_no != "__end__":
                    print(f"📍 Nó executado: {nome_no}")
                    estado_final = estado_no
        
        # Exibe resultados finais
        print()
        print("=" * 80)
        print("📊 RESULTADOS FINAIS")
        print("=" * 80)
        
        if estado_final:
            testes_gerados = estado_final.get("testes_gerados", [])
            cobertura = estado_final.get("percentual_cobertura", 0.0)
            meta = estado_final.get("meta_cobertura", 80.0)
            erros = estado_final.get("erros", [])
            
            print(f"✅ Testes gerados: {len(testes_gerados)}")
            print(f"📈 Cobertura: {cobertura:.1f}% (meta: {meta:.1f}%)")
            
            if erros:
                print(f"⚠️  Erros encontrados: {len(erros)}")
                for erro in erros:
                    print(f"   - {erro}")
            
            # Salva testes gerados
            if testes_gerados:
                arquivo_saida = caminho_arquivo.parent / f"{caminho_arquivo.stem}_GeneratedTests.cs"
                with open(arquivo_saida, 'w', encoding='utf-8') as f:
                    for i, teste in enumerate(testes_gerados, 1):
                        f.write(f"// Teste gerado #{i}\n")
                        f.write(teste)
                        f.write("\n\n")
                
                print(f"💾 Testes salvos em: {arquivo_saida}")
        
        print()
        print("✅ Processo concluído!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
