# Quick Filler

Aplicação web para transcrição revisável de cartões de ponto e holerites em PDF.

## Demonstração

Aplicação publicada:

https://quick-filler-desafio-aua5.onrender.com

A hospedagem gratuita pode levar alguns segundos para iniciar após um período
sem acesso.

## Sobre o projeto

Quick Filler realiza o ciclo completo de transformação de documentos
trabalhistas em dados estruturados:

```text
enviar PDF → processar → revisar → corrigir → baixar
```

O projeto foi iniciado como um desafio técnico e continuou sendo desenvolvido
como projeto de portfólio. O foco está em processamento de PDFs, OCR, parsing
estruturado, validação conservadora, revisão humana e geração de planilhas.

Um dado incerto não deve ser apresentado como confiável. Quando um caractere não
pode ser confirmado, a aplicação preserva a incerteza com `?`. Quando nenhuma
informação útil é recuperada, o processamento termina com uma mensagem de erro
em vez de apresentar uma transcrição vazia como concluída.

## Funcionalidades

- Upload de PDFs com limite de 15 MB
- Validação da assinatura do arquivo PDF
- Seleção entre cartão de ponto e holerite
- Processamento assíncrono com acompanhamento de status
- Extração de texto nativo com PyMuPDF
- OCR com Tesseract para páginas escaneadas
- Interface de revisão em tabelas editáveis
- PDF visível ao lado da transcrição
- Correção individual de células
- Avisos derivados após cada correção
- Destaques amarelos para incertezas e outros problemas
- Destaques vermelhos para datas ou meses não sequenciais
- Exportação em XLSX, CSV e JSON
- Downloads atualizados com as correções feitas na interface
- Tratamento explícito de extrações totalmente vazias
- API documentada e endpoint de saúde
- Execução com Docker Compose
- Testes automatizados com documentos reais selecionados

## Tecnologias

- Python 3.12
- FastAPI
- Uvicorn
- PyMuPDF
- Tesseract OCR
- OpenCV
- OpenPyXL
- Pydantic
- Pytest
- HTML
- CSS
- JavaScript
- Docker
- Docker Compose
- Render

## Arquitetura

A aplicação utiliza um pipeline compartilhado para os dois tipos de documento.
Upload, acompanhamento, revisão, correção e download são comuns; o que muda é o
extrator e a estrutura da planilha.

A API disponibiliza:

```text
POST /api/transcricoes
GET  /api/transcricoes/:id
PUT  /api/transcricoes/:id
GET  /api/transcricoes/:id/pdf
GET  /api/transcricoes/:id/planilha
GET  /healthz
```

Os estados possíveis de processamento são:

```text
processando
concluido
erro
```

## Como executar com Docker

Na raiz do projeto:

```bash
docker compose up --build
```

Acesse:

```text
http://localhost:8000
```

Teste a saúde da aplicação:

```bash
curl http://localhost:8000/healthz
```

Para encerrar:

```bash
docker compose down
```

## Desenvolvimento local

Em Linux ou Codespaces:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --app-dir backend
```

No Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --app-dir backend
```

## Testes

Execute:

```bash
python -m pytest -q
```

Estado atual da suíte:

```text
58 passed, 2 skipped
```

Os testes cobrem parsers, normalização, documentos reais selecionados, avisos,
extrações vazias, exportações e estilos das planilhas.

## Documentação técnica

- [`SOLUCAO.md`](SOLUCAO.md): arquitetura, execução, segurança, limitações e
  decisões técnicas.
- [`PROCESSO.md`](PROCESSO.md): ferramentas utilizadas, erros identificados,
  decisões tomadas e avaliação crítica do desenvolvimento.

## Limitações conhecidas

- A qualidade da extração varia entre layouts.
- O `time-card-04` ainda não fornece dados suficientes para uma transcrição
  confiável e termina com erro legível.
- Alguns layouts de holerite não possuem gabarito visual completo.
- O armazenamento dos jobs é local e em memória.
- Ainda não existe limpeza automática dos arquivos temporários por TTL.
- Rastreabilidade visual e detecção automática do tipo não foram implementadas.
- A versão publicada pode levar alguns segundos para iniciar no plano gratuito.

## Status

O ciclo principal está funcional para os dois tipos de documento, incluindo
revisão por células, correção, avisos e exportação.

O projeto continua evoluindo como portfólio, com prioridade para ampliar a
cobertura de layouts, fortalecer o OCR e melhorar a operação em produção.