"""Gerador de testes unitários usando LLM."""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.llm.factory import criar_llm
from src.test_generator.parser import ParserCodigo


class GeradorTestes:
    """Gerador de testes unitários para código C#."""
    
    def __init__(self):
        """Inicializa o gerador com o LLM configurado."""
        self.llm = criar_llm()
        self.parser = ParserCodigo()
        
        if not self.llm:
            raise ValueError("LLM não configurado. Verifique o arquivo .env")
    
    def _criar_template_prompt(self) -> ChatPromptTemplate:
        """Cria o template de prompt para geração de testes."""
        return ChatPromptTemplate.from_messages([
            ("system", """Você é um especialista em testes unitários para C# (.NET).
Sua tarefa é gerar testes unitários de alta qualidade usando xUnit, NUnit ou MSTest.

Diretrizes:
1. Use xUnit como framework padrão (usando [Fact] ou [Theory])
2. Siga as melhores práticas de testes unitários
3. Teste casos de sucesso, falha e casos extremos
4. Use nomes descritivos para os testes (método_condicao_resultado)
5. Organize os testes usando Arrange-Act-Assert (AAA)
6. Use mocks quando necessário para isolar dependências
7. Retorne APENAS o código C# do teste, sem explicações ou markdown

Formato esperado:
- Declarações 'using' necessárias
- Namespace apropriado
- Classe de teste com sufixo 'Tests'
- Métodos de teste com atributos [Fact] ou [Theory]
"""),
            ("human", """Gere testes unitários para o seguinte código C#:

CÓDIGO FONTE:
{source_code}

TESTES EXISTENTES (se houver):
{existing_tests}

ITERAÇÃO: {iteration}

Gere testes que cubram:
- Casos de sucesso
- Casos de falha/validação
- Casos extremos (null, vazios, limites)
- Diferentes cenários de uso

Retorne APENAS o código C# completo e válido, sem explicações adicionais.""")
        ])
    
    def gerar_teste(
        self,
        codigo_fonte: str,
        testes_existentes: str = "",
        iteracao: int = 0
    ) -> Optional[str]:
        """
        Gera um teste unitário para o código fornecido.
        
        Args:
            codigo_fonte: Código C# a ser testado
            testes_existentes: Testes existentes (para evitar duplicação)
            iteracao: Número da iteração atual
        
        Returns:
            Código do teste gerado ou None em caso de erro
        """
        if not codigo_fonte:
            return None
        
        try:
            # Cria a chain de geração
            prompt = self._criar_template_prompt()
            parser_saida = StrOutputParser()
            
            chain = prompt | self.llm | parser_saida
            
            # Gera o teste
            resultado = chain.invoke({
                "source_code": codigo_fonte,
                "existing_tests": testes_existentes or "Nenhum teste existente.",
                "iteration": iteracao
            })
            
            # Limpa o resultado (remove markdown code blocks se houver)
            codigo_teste = self._limpar_codigo_gerado(resultado)
            
            return codigo_teste
        
        except Exception as e:
            print(f"❌ Erro ao gerar teste: {e}")
            return None
    
    def _limpar_codigo_gerado(self, codigo: str) -> str:
        """
        Limpa o código gerado, removendo markdown e formatação extra.
        
        Args:
            codigo: Código gerado pelo LLM
        
        Returns:
            Código limpo
        """
        # Remove blocos de código markdown
        if "```csharp" in codigo:
            codigo = codigo.split("```csharp")[1]
        elif "```cs" in codigo:
            codigo = codigo.split("```cs")[1]
        elif "```" in codigo:
            codigo = codigo.split("```")[1]
        
        if codigo.endswith("```"):
            codigo = codigo[:-3]
        
        return codigo.strip()


# Alias para compatibilidade
TestGenerator = GeradorTestes
generate_test = GeradorTestes.gerar_teste
