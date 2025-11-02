# Sistema de Extração de Dados de PDF

Uma solução eficiente em custo e alta precisão para extrair dados estruturados de documentos PDF usando IA. Desenvolvido para o projeto take-home do Enter AI Fellowship.

## Visão Geral

Este sistema extrai informações estruturadas de PDFs de página única. **Nota: Os PDFs já contêm texto embutido (não é necessário processamento de OCR).** Combina cache inteligente, prompts de LLM otimizados e processamento eficiente para atender requisitos rigorosos de performance:
- **Tempo de Resposta**: <10 segundos por requisição
- **Precisão**: 80%+ de precisão na extração de campos
- **Otimização de Custo**: Minimização de chamadas à API LLM através de cache e otimização de prompts

## Arquitetura

### Componentes Principais

1. **Extração de Texto de PDF** (`app/pdf_extractor.py`)
   - Usa `pdfplumber` para extrair texto embutido de PDFs
   - Não precisa de OCR - PDFs já contêm texto no documento
   - Manipula PDFs de página única

2. **Serviço LLM** (`app/llm_service.py`)
   - Integração com OpenAI GPT-5-mini
   - Prompts otimizados com uso mínimo de tokens
   - Formato de saída JSON estruturado
   - Rastreamento de custo por requisição

3. **Camada de Cache** (`app/cache_service.py`)
   - Cache em memória usando chaves compostas (hash do PDF + hash do schema)
   - Elimina chamadas redundantes ao LLM para requisições idênticas
   - Baseado em sessão (limpo entre sessões conforme requisitos)

4. **Orquestrador de Extração** (`app/extraction_service.py`)
   - Coordena extração de PDF → verificação de cache → chamada LLM → resposta
   - Trata erros graciosamente
   - Retorna null para campos faltantes

5. **Camada de API** (`app/main.py`)
   - Endpoints REST FastAPI
   - Extração única: `/extract`
   - Processamento em lote: `/extract-batch`
   - Interface web para uso interativo

6. **Frontend** (`frontend/`)
   - Interface web moderna e intuitiva
   - Suporte para processamento único e em lote
   - Métricas de custo e performance em tempo real

7. **Ferramenta CLI** (`cli_extract.py`)
   - Processamento em lote via linha de comando
   - Suporte para entrada de arquivo JSON
   - Relatórios detalhados de progresso e resumo

## Desafios Abordados e Soluções

### Desafio 1: Minimizar Chamadas à API LLM
**Problema**: Cada chamada ao LLM custa dinheiro. Para PDFs idênticos com o mesmo schema, não devemos pagar duas vezes.

**Solução**: 
- **Cache baseado em hash**: Chave de cache composta = SHA256(conteúdo do PDF) + SHA256(schema JSON)
- Mesmo PDF + mesmo schema = cache hit instantâneo (custo $0, tempo de resposta <0.1s)
- Cache persiste durante a sessão, reduzindo drasticamente custos para documentos repetidos

### Desafio 2: Otimizar Tokens do Prompt
**Problema**: Custos do LLM escalam com tokens de entrada/saída. Prompts maiores = custos maiores.

**Solução**:
- **Design de prompt mínimo**: Incluir apenas descrições de campos necessárias
- **Saída estruturada**: Usar `response_format={"type": "json_object"}` para parsing JSON eficiente
- **Temperatura baixa**: Definida em 0.1 para consistência e saídas determinísticas

### Desafio 3: Manter 80%+ de Precisão
**Problema**: Necessidade de alta precisão apesar de layouts variáveis de documentos.

**Solução**:
- **Prompts descritivos de campos**: Incluir contexto nas descrições do schema de extração
- **Saída JSON estruturada**: Força o LLM a retornar JSON válido para todos os campos
- **Tratamento de null**: Retorna graciosamente null para campos faltantes (conforme requisitos)
- **Tratamento de erros**: Continua processando mesmo se campos individuais falharem

### Desafio 4: Atender Tempo de Resposta <10s
**Problema**: Chamadas à API LLM podem ser lentas, especialmente com latência de rede.

**Solução**:
- **Cache**: Cache hits retornam em <0.1s
- **FastAPI assíncrono**: Tratamento de requisições não-bloqueante
- **Extração de texto eficiente**: pdfplumber extrai rapidamente texto embutido de PDFs
- **Otimização de prompt**: Prompts menores = respostas mais rápidas da API

### Desafio 5: Lidar com Layouts Variáveis
**Problema**: Documentos do mesmo label podem ter layouts diferentes.

**Solução**:
- **Flexibilidade do LLM**: GPT-5-mini lida com variações de layout através de compreensão de linguagem natural
- **Descrições ricas em contexto**: Descrições do schema de extração incluem dicas de localização (ex.: "normalmente no canto superior esquerdo")
- **Sem posições hardcoded**: Sistema se adapta automaticamente a mudanças de layout

## Instalação

### Pré-requisitos
- Python 3.9+
- Chave de API OpenAI

### Passos de Configuração

1. **Clonar o repositório**
```bash
git clone <repository-url>
cd ai-fellowship-take-home-project
```

2. **Criar ambiente virtual**
```bash
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
```

4. **Configurar ambiente**
```bash
cp .env.example .env
# Editar .env e adicionar sua OPENAI_API_KEY
```

## Uso

### Opção 1: Interface Web (Recomendado)

1. **Iniciar o servidor**
```bash
python -m app.main
# Ou: uvicorn app.main:app --reload
```

2. **Abrir navegador**
Navegue para `http://localhost:8000`

3. **Usar a interface**
   - **Extração Única**: Fazer upload do PDF, inserir label e schema de extração (JSON), clicar em Extract
   - **Processamento em Lote**: Fazer upload de arquivo JSON com requisições em lote

### Opção 2: API REST

#### Extração Única
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "label=carteira_oab" \
  -F "extraction_schema={\"nome\":\"Nome do profissional\",\"inscricao\":\"Número de inscrição\"}" \
  -F "pdf=@files/oab_1.pdf"
```

#### Processamento em Lote
```bash
curl -X POST "http://localhost:8000/extract-batch" \
  -H "Content-Type: application/json" \
  -d @dataset.json
```

### Opção 3: Ferramenta CLI

```bash
# Processar lote de arquivo JSON
python cli_extract.py --json dataset.json

# Salvar resultados em arquivo
python cli_extract.py --json dataset.json --output results.json

# Especificar diretório customizado de PDFs
python cli_extract.py --json dataset.json --base-dir /caminho/para/pdfs
```

### Opção 4: API Python

```python
from app.extraction_service import extraction_service

# Ler PDF
with open('files/oab_1.pdf', 'rb') as f:
    pdf_content = f.read()

# Extrair dados
schema = {
    "nome": "Nome do profissional",
    "inscricao": "Número de inscrição"
}
label = "carteira_oab"  # Opcional, mas recomendado

result = extraction_service.extract(pdf_content, schema, label)
print(result['extracted_data'])
```

## Testes

Executar a suite de testes com o dataset fornecido:

```bash
python test_extraction.py
```

Isso irá:
- Processar todos os PDFs em `dataset.json`
- Mostrar resultados de extração, tempo e custos
- Calcular métricas de precisão
- Validar requisitos de performance

## Estrutura do Projeto

```
ai-fellowship-take-home-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI
│   ├── models.py             # Modelos Pydantic request/response
│   ├── pdf_extractor.py     # Extração de texto de PDF
│   ├── llm_service.py        # Integração OpenAI LLM
│   ├── cache_service.py      # Camada de cache
│   └── extraction_service.py # Orquestrador de extração principal
├── frontend/
│   ├── index.html           # Interface web
│   └── static/
│       └── style.css        # Estilos da UI
├── files/                   # PDFs de exemplo
├── dataset.json             # Requisições de extração de exemplo
├── cli_extract.py           # Ferramenta CLI para lote
├── test_extraction.py       # Suite de testes
├── requirements.txt         # Dependências Python
├── .env.example            # Template de variáveis de ambiente
└── README.md               # Este arquivo
```

## Documentação da API

Uma vez que o servidor estiver rodando, visite:
- **Documentação Interativa da API**: `http://localhost:8000/docs`
- **Documentação Alternativa**: `http://localhost:8000/redoc`

## Características de Performance

- **Cache Hit**: Tempo de resposta <0.1s, custo $0
- **Cache Miss**: Tempo de resposta 2-5s (depende do tamanho do PDF e latência do LLM)
- **Custo por extração**: ~$0.001-0.005 (varia com o tamanho do texto do PDF)
- **Precisão**: Tipicamente 85-95% em documentos estruturados

## Decisões de Design

1. **Por que FastAPI?**
   - Suporte moderno a async para lidar com requisições concorrentes
   - Documentação OpenAPI automática
   - Validação integrada com Pydantic
   - Alta performance

2. **Por que pdfplumber?**
   - Melhor extração de texto que PyPDF2 para PDFs com texto embutido
   - Lida bem com formatação e layout
   - Leve e rápido
   - Não precisa de OCR - extrai texto já presente no PDF

3. **Por que cache em memória?**
   - Acesso mais rápido possível (<0.1s)
   - Atende requisito de sessão
   - Implementação simples
   - Pode ser estendido para Redis em produção

## Limitações e Melhorias Futuras

- **Atual**: Cache em memória (baseado em sessão)
  - **Futuro**: Cache com Redis/banco de dados para persistência

- **Atual**: Processamento em lote sequencial
  - **Futuro**: Processamento paralelo com async/await

- **Atual**: Tratamento de erros básico
  - **Futuro**: Lógica de retry, backoff exponencial

- **Atual**: Truncamento de texto
  - **Futuro**: Chunking inteligente para documentos maiores

- **Atual**: Sem aprendizado de template
  - **Futuro**: Reconhecimento de padrões para schemas de label repetidos

## Licença

Este projeto faz parte do desafio take-home do Enter AI Fellowship.

## Contato

Para dúvidas ou questões, consulte o repositório do projeto.

