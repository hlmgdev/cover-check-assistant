# Coverage Agent 🤖

Agente inteligente especializado em análise de cobertura de código e geração automática de testes unitários para projetos .NET/C#.

Utiliza **LangChain** e **LangGraph** para orquestrar um fluxo de trabalho em duas fases:
- **Fase 1 (Sem LLM)**: Análise de diff, execução de testes e cálculo de cobertura
- **Fase 2 (Com LLM)**: Correção de testes quebrados e geração de novos testes

## 🚀 Características

- ✅ Análise automática de cobertura de código (diff coverage)
- ✅ Correção inteligente de testes quebrados usando LLM
- ✅ Geração automática de testes unitários de alta qualidade
- ✅ Suporte a múltiplos providers de LLM (OpenAI, Anthropic, Google, Azure, Ollama)
- ✅ Iteração até atingir meta de cobertura configurável (padrão: 80%)
- ✅ Interface interativa para decisões do usuário
- ✅ Compatível com Python 3.13+

## 📋 Pré-requisitos

- Python 3.13.9+
- .NET SDK (8.0+)
- Git
- Projeto .NET com testes unitários (xUnit, NUnit ou MSTest)

## 🛠️ Instalação

1. Clone o repositório:
```bash
cd c:/ReposPython/_IA/antigravity
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env-example .env
# Edite o .env com suas chaves de API
```

## ⚙️ Configuração

Edite o arquivo `.env` com suas configurações:

```env
# Provider de LLM (openai, anthropic, google, azure, ollama)
LLM_PROVIDER=openai

# Chave de API (dependendo do provider)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Configurações do agente
TARGET_COVERAGE_PERCENTAGE=80
MAX_ITERATIONS=5
AUTO_FIX_BROKEN_TESTS=true
```

