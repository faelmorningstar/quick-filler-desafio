# Quick Filler

Aplicação web para transcrição revisável de cartões de ponto e holerites.

## Demonstração

Aplicação publicada: https://quick-filler-desafio-aua5.onrender.com

## Sobre o Projeto

Quick Filler é uma aplicação web para extração, revisão e exportação de dados estruturados a partir de PDFs de holerites e cartões de ponto.

O projeto foi desenvolvido como desafio técnico, com foco em leitura de PDFs, parsing estruturado, validação de dados e geração de planilhas.

## Funcionalidades

- Upload de PDFs de holerite e cartão de ponto
- Processamento de documentos com extração estruturada
- Exibição dos dados em formato revisável
- Exportação dos resultados em planilha
- Interface e cabeçalhos das planilhas em português-BR
- Testes automatizados para validar documentos reais
- Deploy público da aplicação

## Tecnologias

- Python
- FastAPI
- PyMuPDF
- OpenPyXL
- Pytest
- HTML, CSS e JavaScript
- Docker
- Render

## Destaques Técnicos

- Extração de texto e coordenadas de PDFs
- Separação entre holerites e cartões de ponto
- Validação para evitar dados inventados
- Preservação do contrato original da API em inglês
- Testes com arquivos reais do desafio
- Documentação do processo de desenvolvimento e decisões técnicas

## Como executar localmente no Windows

Estes comandos devem ser executados em um ambiente local com Python instalado. No editor web do GitHub, é possível apenas editar arquivos e enviar commits.

Na raiz do projeto, instale as dependências:

```powershell
python -m pip install -r requirements.txt

## Status

Projeto entregue como desafio técnico e mantido em evolução para portfólio.

A versão atual valida o fluxo principal com documentos reais selecionados. Melhorias futuras incluem ampliar a cobertura para mais layouts, fortalecer o parser e evoluir a interface de revisão.