# Solução — Quick Filler

## Como executar

O modo recomendado utiliza Docker com Docker Compose:

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8000
```

A saúde da aplicação pode ser verificada em:

```text
GET /healthz
```

Resposta esperada:

```json
{"status": "ok"}
```

Para encerrar e remover o contêiner:

```bash
docker compose down
```

### Desenvolvimento local

Em Linux ou Codespaces:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --app-dir backend
```

No Windows, a ativação do ambiente virtual é:

```powershell
.venv\Scripts\activate
```

Depois, a aplicação pode ser iniciada com:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
```

## Arquitetura

Existe um único ciclo compartilhado para cartão de ponto e holerite:

```text
upload → processamento → consulta → revisão → correção → exportação
```

O arquivo `backend/app/transcription.py` concentra a seleção da extração
específica de cada documento. API, armazenamento temporário, acompanhamento do
processamento, revisão e download são compartilhados pelos dois tipos.

O processamento é iniciado após a resposta HTTP `202 Accepted`. Enquanto o job
está em andamento, a interface consulta o endpoint de transcrição até receber
`concluido` ou `erro`.

Os estados da API permanecem dentro do contrato obrigatório:

- `processando`;
- `concluido`;
- `erro`.

Uma extração totalmente vazia não é apresentada como concluída. Nesse caso, o
job termina em `erro` com uma mensagem legível sobre a insuficiência da
extração ou do OCR.

## Interface de revisão

A revisão acontece em tabelas editáveis específicas para cartão de ponto e
holerite, com o PDF visível ao lado.

No cartão de ponto, a interface apresenta:

- página;
- data;
- entradas e saídas em colunas;
- células editáveis;
- avisos relacionados às batidas.

No holerite, a interface apresenta:

- página;
- mês e ano;
- código da verba;
- descrição;
- referência;
- valor;
- bases e totais.

As correções são enviadas para:

```text
PUT /api/transcricoes/:id
```

Depois do salvamento, os avisos são recalculados. Os downloads em XLSX, CSV e
JSON utilizam os dados já corrigidos.

Caracteres incertos e outros problemas recebem destaque amarelo. Problemas de
sequencialidade recebem destaque vermelho e têm prioridade quando as duas
situações ocorrem na mesma linha ou página.

## Extração

- Páginas com cobertura textual útil usam PyMuPDF.
- Páginas vazias ou com camada textual insuficiente seguem para OCR com
  Tesseract.
- A imagem Docker instala o Tesseract e o idioma português.
- Valores monetários, datas e horários permanecem como strings.
- Os valores originais são preservados separadamente dos valores normalizados
  quando o contrato exige campos `_raw`.
- Caracteres que não puderam ser confirmados podem ser representados por `?`,
  sem tentativa de inventar o conteúdo.
- O layout de `payroll-03` possui suporte geométrico validado por um gabarito
  mínimo.
- Outros layouts usam estratégias conservadoras e podem apresentar qualidade
  diferente.

## Exportação

A aplicação permite baixar os dados nos formatos:

- XLSX;
- CSV;
- JSON.

O XLSX utiliza cabeçalho branco em negrito sobre fundo `#173772`.

As linhas recebem:

- fundo `#FFF3CD` para caracteres incertos, batidas ímpares ou páginas vazias;
- fundo `#F8D7DA` para datas ou meses não sequenciais;
- borda esquerda `#DC3545` na primeira célula dos problemas sequenciais.

Quando uma linha possui aviso amarelo e vermelho ao mesmo tempo, o vermelho
prevalece.

## Segurança e retenção

- Limite de upload: 15 MB.
- O conteúdo precisa começar com a assinatura `%PDF-`.
- O nome original do arquivo não é reutilizado no servidor.
- Cada job recebe um identificador aleatório.
- Erros retornados não incluem o conteúdo do documento nem dados pessoais.
- O índice das transcrições fica somente em memória e é perdido quando o
  processo reinicia.
- Os PDFs permanecem no diretório temporário durante a vida útil do contêiner e
  são eliminados quando ele é removido.
- A demonstração ainda não possui limpeza automática por tempo.

Em produção, seria necessário utilizar armazenamento privado, expiração dos
jobs e exclusão automática dos PDFs por TTL.

## Testes escolhidos

A suíte possui:

```text
58 passed, 2 skipped
```

Os testes cobrem:

- contrato dos dados;
- normalização;
- parsers;
- documentos reais selecionados;
- preservação da ordem;
- avisos derivados;
- extrações totalmente vazias;
- exibição inline do PDF;
- exportação;
- cores e prioridade dos avisos no XLSX.

O teste de integração de `payroll-03` verifica competência, verbas, totais e
bases porque esses foram erros de alto impacto identificados durante o
desenvolvimento.

O Docker também foi validado manualmente com:

- construção completa da imagem;
- inicialização pelo Docker Compose;
- resposta do `/healthz`;
- processamento de holerite;
- processamento de cartão de ponto com texto reconhecido;
- tratamento conservador do `time-card-04`.

## Limitações e cortes conscientes

- `payroll-01` é uma ficha financeira, considerada funcionalidade bônus, e é
  recusado de forma conservadora em vez de produzir campos misturados.
- O OCR de `time-card-04`, manuscrito e pouco nítido, ainda não recupera dados
  suficientes. A aplicação encerra esse caso com erro legível, em vez de
  apresentar uma transcrição vazia como concluída.
- Os fallbacks de `payroll-02` e `payroll-04` não possuem gabarito visual
  completo.
- A qualidade da extração não é uniforme entre todos os layouts.
- A interface e os cabeçalhos das planilhas usam português-BR, enquanto JSON e
  API preservam o contrato literal exigido.
- O parser interno reconhece blocos `MÊS` e `ACERTO` para posicionar referências
  textuais como `JULHO/18` e `S/13 SAL`, mas a resposta HTTP permanece no
  formato obrigatório `pages/fields/bases`.
- O armazenamento não é compartilhado entre réplicas.
- O estado dos jobs não sobrevive à reinicialização do processo.
- Ainda não há limpeza automática dos arquivos temporários por TTL.
- Não foram implementadas rastreabilidade visual nem detecção automática do
  tipo de documento.

Esses cortes preservam o ciclo completo e evitam apresentar como confiáveis
dados que a aplicação não conseguiu confirmar.