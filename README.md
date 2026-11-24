# chatbot-rag

Chatbot de atendimento com **RAG** (Retrieval-Augmented Generation) para a doceria **Briga do Biel**. O sistema indexa uma base de conhecimento em PDF (cardápio, preços, contato, perguntas frequentes) e busca os trechos mais relevantes para responder perguntas de clientes.

> Projeto de estudo. A etapa de busca está pronta; a geração de respostas com o Claude e o endpoint de chat ainda estão em desenvolvimento.

## Como funciona

```
PDF ──► extração de texto ──► chunks (600 caracteres, 100 de sobreposição)
                                   │
                                   ▼
                     embeddings (Sentence Transformers)
                                   │
                                   ▼
              data/embeddings.npy  +  data/chunks.json
                                   │
pergunta ──► embedding ──► similaridade de cosseno ──► top-k trechos ──► Claude (em breve)
```

1. **Ingestão** ([ingest.py](src/chatbot_rag/ingest.py)): lê todos os PDFs de `data/`, normaliza os espaços, divide o texto em trechos com sobreposição e gera um vetor para cada trecho.
2. **Busca** ([retriever.py](src/chatbot_rag/retriever.py)): transforma a pergunta em vetor e compara com os vetores salvos. Como estão normalizados, o produto escalar equivale à similaridade de cosseno. Retorna os `TOP_K` trechos com maior pontuação.
3. **Geração** (planejada): enviar a pergunta e os trechos ao Claude, que responde apenas com base neles.
4. **API** ([main.py](src/chatbot_rag/main.py)): aplicação FastAPI. Por enquanto só expõe `/health`.

## Tecnologias

- Python 3.11+
- [FastAPI](https://fastapi.tiangolo.com/): API HTTP
- [Sentence Transformers](https://www.sbert.net/): embeddings, com o modelo multilíngue `paraphrase-multilingual-MiniLM-L12-v2`
- [pypdf](https://pypdf.readthedocs.io/): extração de texto dos PDFs
- NumPy: armazenamento dos vetores e cálculo de similaridade
- [Anthropic SDK](https://docs.claude.com/): geração das respostas com o Claude

## Estrutura

```
chatbot-rag/
├── data/
│   ├── *.pdf              # base de conhecimento (não versionada)
│   ├── chunks.json        # trechos gerados pela ingestão
│   └── embeddings.npy     # vetores dos trechos
├── src/chatbot_rag/
│   ├── config.py          # caminhos e parâmetros
│   ├── ingest.py          # constrói o índice
│   ├── retriever.py       # busca semântica
│   └── main.py            # API FastAPI
├── tests/
│   └── teste_busca.py     # teste manual da busca
├── .env.example
└── pyproject.toml
```

## Instalação

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

Copie o arquivo de exemplo e coloque sua chave da API da Anthropic:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sua-chave-aqui
```

## Uso

### 1. Gerar o índice

Coloque o(s) PDF(s) em `data/` e rode:

```bash
python -m chatbot_rag.ingest
```

Rode de novo sempre que o PDF ou os parâmetros de chunking mudarem.

### 2. Testar a busca

```bash
python tests/teste_busca.py
```

Exemplo de saída para "Qual o valor dos brigadeiros alcoolicos?":

```
0.53 | página 3 | ingredientes. 10. Perguntas frequentes P: Quanto custa o cento de brigadeiros? R: Depende da linha: ...
0.448 | página 1 | igas envolvendo artistas. Os brigadeiros são feitos com ingredientes selecionados e muito cuidado em ...
```

O teste mostra só os primeiros 100 caracteres de cada trecho. A resposta ("Alcoólicos R$ 300") aparece mais adiante no texto do primeiro resultado.

### 3. Subir a API

```bash
fastapi dev src/chatbot_rag/main.py
```

Acesse `http://127.0.0.1:8000/health` ou a documentação interativa em `http://127.0.0.1:8000/docs`.

## Configuração

Os parâmetros ficam em [config.py](src/chatbot_rag/config.py):

| Parâmetro              | Valor padrão                             | Descrição                                   |
|------------------------|------------------------------------------|---------------------------------------------|
| `EMBEDDING_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings                        |
| `CHUNK_SIZE`           | `600`                                    | Tamanho máximo de cada trecho, em caracteres |
| `CHUNK_OVERLAP`        | `100`                                    | Sobreposição entre trechos vizinhos         |
| `TOP_K`                | `2`                                      | Quantidade de trechos retornados na busca   |
| `CLAUDE_MODEL`         | `claude-haiku-5-5`                       | Modelo usado para gerar as respostas        |

## Próximos passos

- [ ] Endpoint `POST /chat`: buscar os trechos e gerar a resposta com o Claude
- [ ] Dividir os trechos por seção do documento (linhas do cardápio, perguntas frequentes) em vez de por tamanho fixo
- [ ] Avaliar `TOP_K` entre 3 e 4
- [ ] Transformar `teste_busca.py` em testes automatizados com pytest
