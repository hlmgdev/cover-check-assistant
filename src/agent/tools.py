"""Ferramentas disponíveis para o agente."""

from typing import List, Dict, Any
from langchain_core.tools import tool


@tool
def analisar_estrutura_codigo(codigo: str) -> Dict[str, Any]:
    """
    Analisa a estrutura do código C# e identifica classes, métodos e dependências.
    
    Args:
        codigo: Código fonte C# a ser analisado
    
    Returns:
        Dicionário com informações sobre a estrutura do código
    """
    # Implementação básica - pode ser expandida
    classes = []
    metodos = []
    
    linhas = codigo.split('\n')
    classe_atual = None
    
    for linha in linhas:
        linha_limpa = linha.strip()
        # Detecta classes
        if 'class ' in linha_limpa and '{' in linha_limpa:
            nome_classe = linha_limpa.split('class ')[1].split()[0].split('{')[0].strip()
            classes.append(nome_classe)
            classe_atual = nome_classe
        # Detecta métodos públicos
        elif 'public ' in linha_limpa and '(' in linha_limpa and '{' in linha_limpa:
            nome_metodo = linha_limpa.split('(')[0].split()[-1].strip()
            if nome_metodo and classe_atual:
                metodos.append(f"{classe_atual}.{nome_metodo}")
    
    return {
        "classes": classes,
        "metodos": metodos,
        "total_linhas": len(linhas),
        "complexidade": "medio"  # Placeholder
    }


@tool
def validar_codigo_teste(codigo_teste: str) -> Dict[str, Any]:
    """
    Valida se o código de teste gerado é sintaticamente correto.
    
    Args:
        codigo_teste: Código de teste C# a ser validado
    
    Returns:
        Dicionário com resultado da validação
    """
    # Validação básica - verifica estrutura mínima
    tem_using = 'using ' in codigo_teste
    tem_classe_teste = '[Fact]' in codigo_teste or '[Test]' in codigo_teste or '[TestMethod]' in codigo_teste
    tem_metodo_teste = 'public void' in codigo_teste or 'public async Task' in codigo_teste
    
    eh_valido = tem_using and tem_classe_teste and tem_metodo_teste
    
    erros = []
    if not tem_using:
        erros.append("Faltam declarações 'using'")
    if not tem_classe_teste:
        erros.append("Falta atributo de teste ([Fact], [Test] ou [TestMethod])")
    if not tem_metodo_teste:
        erros.append("Falta método de teste público")
    
    return {
        "eh_valido": eh_valido,
        "erros": erros,
        "tem_using": tem_using,
        "tem_classe_teste": tem_classe_teste,
        "tem_metodo_teste": tem_metodo_teste
    }


# Aliases para compatibilidade com código existente
analyze_code_structure = analisar_estrutura_codigo
validate_test_code = validar_codigo_teste
