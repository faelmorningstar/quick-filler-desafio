# Solução - Quick Filler

## Como executar

Requisito recomendado: Docker Desktop com Docker Compose.

```bash
docker compose up --build
```

Acesse `http://localhost:8000`. A saúde da aplicação pode ser verificada em
`GET /healthz`.

Para desenvolvimento local:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=backend
uvicorn app.main:app --reload
```

## Arquitetura

Existe um único ciclo para cartão de ponto e holerite: upload, processamento,
consulta, correção e exportação. `backend/app/transcription.py` concentra a
extração específica de cada documento; API, armazenamento temporário, revisão
e download são compartilhados.

O processamento é disparado após a resposta `202`, e o cliente consulta o job
até `concluido` ou `erro`. O armazenamento é em memória e em diretório
temporário, suficiente para demonstração de uma única instância.

## Extração

- Páginas com cobertura textual útil usam PyMuPDF.
- Páginas vazias ou com camada textual insuficiente caem para Tesseract.
- O Docker instala português e inglês para OCR.
- Valores e horários permanecem strings.
- Tokens de OCR com baixa confiança são substituídos por `?`, sem tentativa de
  adivinhar o caractere.
- O layout de `payroll-03` possui suporte geométrico validado por um gabarito
  mínimo. Outros layouts usam fallback conservador.

## Segurança e retenção

- Limite de upload: 15 MB.
- O conteúdo precisa começar com a assinatura `%PDF-`.
- O nome original não é reutilizado no servidor.
- Erros retornados não incluem conteúdo nem dados pessoais.
- PDFs e transcrições ficam no diretório temporário da instância e na memória.
  São descartados quando o contêiner é reiniciado. Em produção, seria necessário
  um job periódico de expiração e armazenamento privado com TTL.

## Testes escolhidos

Os testes unitários cobrem contrato, normalização e avisos. O teste de integração
de `payroll-03` verifica competência, três verbas e bases porque esses são os
erros de maior impacto observados no parser anterior.

## Limitações e cortes conscientes

- `payroll-01` é ficha financeira, funcionalidade bônus, e é recusado de forma
  conservadora pelo extrator obrigatório em vez de produzir campos misturados.
- O OCR de `time-card-04`, manuscrito e pouco nítido, precisa de revisão humana.
- Os fallbacks de `payroll-02` e `payroll-04` não possuem gabarito completo.
- A interface usa um editor JSON ao lado do PDF; o ciclo de correção funciona,
  mas não é a tabela por célula ideal do produto.
- A interface e os cabeçalhos das planilhas usam português-BR; JSON e API
  preservam o contrato literal em inglês exigido pelo avaliador.
- O parser interno reconhece blocos `MÊS` e `ACERTO` para posicionar referências
  textuais como `JULHO/18` e `S/13 SAL`, mas a resposta HTTP permanece no
  formato obrigatório `pages/fields/bases`.
- O armazenamento não é compartilhado entre réplicas e não sobrevive a restart.
- Não foi implementada rastreabilidade visual nem detecção automática do tipo.

Esses cortes preservam o ciclo inteiro e evitam apresentar dados não confirmados.
