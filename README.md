# Briga do Biel: chatbot RAG

Assistente de atendimento para a doceria **Briga do Biel** usando **RAG** (Retrieval-Augmented Generation). O sistema indexa uma base de conhecimento em PDF (cardápio, preços, contato, perguntas frequentes), encontra os trechos mais relevantes para cada pergunta e usa o **Claude** para escrever uma resposta baseada apenas nesses trechos, citando as fontes.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual o valor dos brigadeiros alcoolicos?"}'
```

```json
{
  "answer": "Os brigadeiros alcoólicos custam **R$ 300,00 o cento**, conforme a linha Alcoólicos [1][3]. O único sabor alcoólico citado no documento é o de Amarula, e a venda é restrita a maiores de 18 anos [1][3].",
  "sources": [
    { "source": "brigadobiel.pdf", "page": 3, "score": 0.53 },
    { "source": "brigadobiel.pdf", "page": 1, "score": 0.448 },
    { "source": "brigadobiel.pdf", "page": 2, "score": 0.399 },
    { "source": "brigadobiel.pdf", "page": 3, "score": 0.31 }
  ]
}
```

> Projeto de estudo.

## Sumário

- [Como funciona](#como-funciona)
- [Tecnologias](#tecnologias)
- [Estrutura](#estrutura)
- [Instalação](#instalação)
- [Uso](#uso)
- [API](#api)
- [Configuração](#configuração)
- [Problemas comuns](#problemas-comuns)
- [Próximos passos](#próximos-passos)

## Como funciona

O projeto tem duas fases: a **indexação**, feita uma vez, e a **consulta**, feita a cada pergunta.

```
INDEXAÇÃO  (python -m chatbot_rag.ingest)

  data/*.pdf ─► extrai texto ─► divide em trechos ─► gera embeddings ─► data/chunks.json
                (pypdf)          600 caracteres,      (Sentence          data/embeddings.npy
                                 100 de sobreposição   Transformers)

CONSULTA  (POST /chat)

  pergunta ─► embedding ─► similaridade de cosseno ─► top-k trechos ─► Claude ─► resposta + fontes
                           com todos os trechos         (TOP_K = 4)
```

| Etapa | Arquivo | O que faz |
|-------|---------|-----------|
| Ingestão | [ingest.py](src/chatbot_rag/ingest.py) | Lê os PDFs de `data/`, normaliza os espaços, divide em trechos com sobreposição (cortando em espaços para não quebrar palavras) e salva os embeddings normalizados. |
| Busca | [retriever.py](src/chatbot_rag/retriever.py) | Gera o embedding da pergunta e calcula o produto escalar com todos os trechos. Como os vetores estão normalizados, isso equivale à similaridade de cosseno. Retorna os `TOP_K` melhores. |
| Geração | [llm.py](src/chatbot_rag/llm.py) | Monta um contexto numerado (`[1]`, `[2]`…) com os trechos e pede ao Claude que responda **só** com base nele, em português e citando as fontes. Se a informação não estiver no contexto, ele diz que não encontrou. |
| API | [main.py](src/chatbot_rag/main.py) | Aplicação FastAPI com `/health` e `/chat`. O índice e o modelo de embeddings são carregados uma vez, quando o servidor sobe. |

## Tecnologias

- **Python 3.11+**
- [FastAPI](https://fastapi.tiangolo.com/): API HTTP e documentação interativa
- [Sentence Transformers](https://www.sbert.net/): embeddings com o modelo multilíngue `paraphrase-multilingual-MiniLM-L12-v2`, que funciona bem em português
- [pypdf](https://pypdf.readthedocs.io/): extração de texto dos PDFs
- **NumPy**: armazenamento dos vetores e cálculo de similaridade (sem banco vetorial, o que basta para uma base pequena)
- [Anthropic SDK](https://docs.claude.com/): geração das respostas com o Claude (`claude-haiku-5-5`)

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
│   ├── llm.py             # geração da resposta com o Claude
│   └── main.py            # API FastAPI
├── tests/
│   └── teste_busca.py     # teste manual: busca + resposta
├── .env.example
└── pyproject.toml
```

## Instalação

Requisitos: Python 3.11+ e uma chave da API da Anthropic.

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

Crie o `.env` a partir do exemplo e coloque sua chave:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sua-chave-aqui
```

O `.env` está no `.gitignore`. Nunca faça commit da chave.

## Uso

### 1. Gerar o índice

Coloque o(s) PDF(s) em `data/` e rode:

```bash
python -m chatbot_rag.ingest
```

Rode de novo sempre que o PDF ou os parâmetros de divisão (`CHUNK_SIZE`, `CHUNK_OVERLAP`) mudarem.

### 2. Testar pelo terminal

```bash
python tests/teste_busca.py
```

O script mostra os trechos encontrados, com a pontuação e a página, e em seguida a resposta do Claude:

```
0.53 | página 3 | ingredientes. 10. Perguntas frequentes P: Quanto custa o cento de brigadeiros? R: Depende da linha:
0.448 | página 1 | igas envolvendo artistas. Os brigadeiros são feitos com ingredientes selecionados e muito cuidado em
0.399 | página 2 | Briga do Biel — Base de Conhecimento — página 2  Ninho com Uva: combinação perfeita.  Banoffee: do
0.31 | página 3 | Briga do Biel — Base de Conhecimento — página 3 9. O que os clientes dizem Os clientes elogiam princ
Os brigadeiros alcoólicos custam R$ 300 o cento [1]. O único sabor alcoólico citado no documento é o de Amarula, vendido apenas para maiores de 18 anos [1].
```

Cada trecho aparece cortado em 100 caracteres, mas o Claude recebe o texto completo.

### 3. Subir a API

```bash
fastapi dev src/chatbot_rag/main.py
```

Espere aparecer `Application startup complete` no terminal (o modelo de embeddings leva alguns segundos para carregar) e abra **http://127.0.0.1:8000/docs** para testar pelo navegador.

## API

| Método | Rota      | Descrição |
|--------|-----------|-----------|
| `GET`  | `/health` | Verifica se a API está no ar. Retorna `{"status": "ok"}`. |
| `POST` | `/chat`   | Recebe uma pergunta e devolve a resposta e os trechos usados. |
| `GET`  | `/docs`   | Documentação interativa (Swagger) gerada pelo FastAPI. |

**`POST /chat`**

Requisição:

```json
{ "question": "Qual o sabor mais pedido?" }
```

Resposta:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `answer` | string | Resposta do Claude, com citações `[n]` que apontam para a posição do trecho em `sources` |
| `sources[].source` | string | Nome do PDF |
| `sources[].page` | int | Página do trecho |
| `sources[].score` | float | Similaridade com a pergunta (de -1 a 1; quanto maior, mais relevante) |

## Configuração

Os parâmetros ficam em [config.py](src/chatbot_rag/config.py):

| Parâmetro              | Valor                                    | Descrição |
|------------------------|------------------------------------------|-----------|
| `EMBEDDING_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings |
| `CHUNK_SIZE`           | `600`                                    | Tamanho máximo de cada trecho, em caracteres |
| `CHUNK_OVERLAP`        | `100`                                    | Sobreposição entre trechos vizinhos |
| `TOP_K`                | `4`                                      | Quantos trechos são enviados ao Claude |
| `CLAUDE_MODEL`         | `claude-haiku-5-5`                       | Modelo usado para gerar as respostas |

Ao mudar o `EMBEDDING_MODEL_NAME`, `CHUNK_SIZE` ou `CHUNK_OVERLAP`, gere o índice de novo.

**Por que `TOP_K = 4`?** Com 2, o trecho que contém "3.4 Linha Alcoólicos — R$ 300,00 o cento" ficava em 3º lugar e não era enviado. Ele divide os 600 caracteres com a lista Gourmet e os cookies, o que dilui o embedding. Com 4, ele sempre entra, e o Claude ignora os trechos irrelevantes.

## Problemas comuns

**`AuthenticationError: 401 ... Invalid bearer token`**
A chave usada não é válida. Se a chave do `.env` estiver correta, verifique se existe uma `ANTHROPIC_API_KEY` definida na sessão do terminal: o `load_dotenv()` **não** substitui variáveis que já existem.

```powershell
$env:ANTHROPIC_API_KEY.Length        # se mostrar um número, existe uma chave na sessão
Remove-Item Env:ANTHROPIC_API_KEY    # remove e passa a valer a do .env
```

**`ERR_CONNECTION_REFUSED` em `127.0.0.1:8000`**
O servidor não está rodando ou ainda está carregando o modelo. Confira se o `fastapi dev` está ativo e se já apareceu `Application startup complete`.

**`{"detail": "Not Found"}` em `http://127.0.0.1:8000/`**
É normal: a raiz não tem rota. Use `/docs` ou `/chat`.

**`RuntimeError: Índice não encontrado`**
O índice ainda não foi gerado. Rode `python -m chatbot_rag.ingest`.

## Próximos passos

- [x] Busca semântica com embeddings
- [x] Geração de respostas com o Claude, com citação das fontes
- [x] Endpoint `POST /chat`
- [ ] Dividir os trechos por seção do documento (linhas do cardápio, perguntas frequentes) em vez de por tamanho fixo
- [ ] Devolver o texto dos trechos em `sources` para facilitar a conferência
- [ ] Redirecionar `/` para `/docs`
- [ ] Histórico de conversa (perguntas de acompanhamento)
- [ ] Transformar `teste_busca.py` em testes automatizados com pytest, simulando a chamada ao Claude
