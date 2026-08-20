# Processo e uso de IA

## Ferramentas

- ChatGPT/Codex: diagnóstico dos PDFs, revisão arquitetural, implementação
  assistida e criação de testes.
- PyMuPDF: camada textual, palavras e coordenadas.
- Tesseract: fallback para páginas escaneadas.
- Pytest: testes de unidade e integração.

## Erros e correções do agente

1. Inicialmente foi sugerido que um PDF com camada textual provavelmente
   permitiria extração direta. A presença de texto não comprova cobertura. Isso
   foi percebido ao comparar visualmente `payroll-04` com os 85 caracteres da
   camada textual, que continham apenas o protocolo judicial. A solução passou
   a auditar quantidade de texto e palavras antes de escolher o extrator.
2. A investigação inicial tratou `payroll-01` como holerite comum. A inspeção
   visual e o enunciado mostraram que ele é uma ficha financeira anual, bônus do
   desafio. Ele foi retirado do caminho obrigatório.
3. O agrupamento `um Y = um registro` juntou rendimento, desconto e resultado
   que ocupavam a mesma altura. O erro apareceu em labels contendo vários campos.
   A correção foi preservar X e segmentar as regiões da página.

## Partes revistas manualmente

O gabarito da página 1 de `payroll-03` foi conferido visualmente, incluindo o
código `/314`, totais e bases. As limitações foram escritas explicitamente para
que a entrega não prometa precisão não medida.

## Decisões com mais de uma resposta razoável

1. Texto nativo ou OCR: foi escolhido texto nativo somente quando há cobertura
   mínima, com OCR por página como fallback. OCR indiscriminado perderia
   informação de PDFs digitais.
2. Banco ou memória: memória e diretório temporário foram escolhidos para o
   prazo e execução em instância única. Banco seria melhor para múltiplas réplicas.
3. Generalização ou layouts conhecidos: foi escolhido um parser geométrico
   validado para um layout e fallback conservador para os demais. Regras muito
   genéricas tinham produzido dados incorretos com aparência válida.

## O que quebra primeiro em produção?

O armazenamento em memória: jobs desaparecem em restart e não são compartilhados
entre réplicas. OCR simultâneo também pode consumir CPU e memória rapidamente.

## Onde não confio plenamente?

Nos documentos escaneados, especialmente `time-card-04`, e nos layouts de
holerite ainda sem gabarito integral. Esses casos precisam de revisão humana e
mais testes reais antes de uso fora da demonstração.

## Validação posterior do payroll-02

A comparação visual das cinco páginas confirmou todos os códigos e valores,
mas mostrou dois erros de estrutura: referências textuais estavam anexadas à
descrição e os demonstrativos `MÊS` e `ACERTO` eram misturados. A correção
passou a usar as colunas geométricas da tabela, preservou os dois blocos e
separou cada item do resumo. Uma tentativa de traduzir as chaves públicas foi
revertida ao conferir que o contrato HTTP é literal; apenas interface e
cabeçalhos ficam em português-BR. Após a alteração, os testes e o fluxo real da
API passaram.
