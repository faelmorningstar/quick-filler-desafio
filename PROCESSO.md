# Processo e uso de IA

## Ferramentas utilizadas

- ChatGPT e Codex: diagnóstico dos PDFs, discussão de arquitetura, implementação
  assistida, revisão de código e elaboração de testes.
- VS Code e GitHub Codespaces: edição, terminal, execução da aplicação e
  organização dos commits.
- PyMuPDF: leitura da camada textual, palavras e coordenadas.
- Tesseract: OCR de páginas escaneadas.
- OpenCV: preparação de imagens para OCR.
- FastAPI e Uvicorn: API e execução da aplicação.
- OpenPyXL: geração e formatação das planilhas.
- Pytest: testes unitários, integração e regressão.
- Docker e Docker Compose: validação do ambiente completo.
- Render: publicação da aplicação.

## Como a IA foi utilizada

A IA foi usada como apoio de desenvolvimento, não como fonte automática de
verdade. As sugestões foram verificadas por:

- inspeção visual dos PDFs;
- comparação com o contrato obrigatório;
- execução de documentos reais;
- testes automatizados;
- inspeção dos JSONs e planilhas gerados;
- validação manual da interface;
- revisão do comportamento dentro do Docker.

Quando uma sugestão não correspondia ao documento, ao contrato ou ao resultado
real, ela era descartada ou corrigida.

## Três erros ou caminhos inadequados do agente

### 1. Confundir presença de texto com cobertura suficiente

Inicialmente, o agente sugeriu que um PDF com camada textual provavelmente
permitiria extração direta. Essa conclusão era imprecisa: possuir algum texto
não significa que o conteúdo visual esteja representado integralmente.

O problema foi percebido ao comparar visualmente `payroll-04` com os poucos
caracteres recuperados da camada textual, que representavam apenas parte do
documento.

A solução passou a avaliar a cobertura textual por página e usar OCR quando o
texto nativo fosse vazio ou insuficiente.

### 2. Aceitar uma revisão em JSON bruto como ciclo suficiente

A primeira versão permitia editar a transcrição como JSON ao lado do PDF. O
ciclo técnico de correção funcionava, mas essa interface transferia ao usuário
a responsabilidade de compreender a estrutura interna da API.

O feedback recebido após o desafio mostrou que a revisão precisava ocorrer por
células, seguindo a estrutura de cada documento.

A interface foi reescrita para apresentar:

- dias e batidas no cartão de ponto;
- competência, verbas, referências, valores, bases e totais no holerite;
- PDF visível ao lado;
- células editáveis;
- avisos legíveis;
- destaques amarelos e vermelhos;
- downloads que refletem as correções.

### 3. Considerar concluída uma extração totalmente vazia

A primeira implementação permitia que um documento escaneado terminasse com
status `concluido` mesmo sem retornar dias ou batidas. O sistema não inventava
valores, mas também não comunicava corretamente que a extração havia falhado.

A correção separou dois casos:

- extração parcial: pode terminar como `concluido`, com revisão e avisos;
- extração completamente vazia: termina como `erro`, com mensagem legível.

Não foi criado um quarto status porque o contrato HTTP permite apenas
`processando`, `concluido` e `erro`. Testes de regressão foram adicionados para
cartão de ponto e holerite.

## Partes verificadas ou ajustadas manualmente

O gabarito da página 1 de `payroll-03` foi conferido visualmente, incluindo:

- competência;
- códigos e descrições;
- referências;
- valores;
- código `/314`;
- totais;
- bases de INSS, IRRF e FGTS.

O fluxo da interface também foi testado manualmente:

```text
upload → processamento → revisão → edição → salvamento → download
```

Foram conferidos downloads em JSON após alterações feitas nas células do cartão
e do holerite.

Os destaques foram verificados manualmente para:

- batidas ímpares;
- caracteres com `?`;
- páginas vazias;
- meses não sequenciais;
- prioridade do vermelho sobre o amarelo.

O Docker foi executado com documentos reais para confirmar que a aplicação não
dependia apenas do ambiente do Codespaces.

A documentação foi revisada para remover afirmações que deixaram de ser
verdadeiras, como a existência de um editor JSON como interface principal.

## Três decisões com mais de uma resposta razoável

### 1. Quando usar texto nativo ou OCR

Foi escolhido texto nativo somente quando a página apresenta cobertura textual
útil. Páginas vazias ou insuficientes seguem para OCR.

Aplicar OCR em todos os documentos simplificaria o pipeline, mas poderia perder
informações precisas já presentes em PDFs digitais e aumentaria o custo de
processamento.

### 2. Como representar uma extração vazia

O contrato não permite um status adicional como `revisao-necessaria`.

A decisão foi:

- manter `concluido` para dados parciais que podem ser revisados;
- usar `erro` quando nenhum dado útil é recuperado;
- apresentar avisos derivados separadamente do status.

Essa escolha preserva o contrato e evita apresentar uma falha total como
sucesso.

### 3. Banco de dados ou armazenamento temporário

Foi escolhido armazenamento em memória e diretório temporário para uma
demonstração executada em uma única instância.

Um banco de dados seria mais adequado para múltiplas réplicas, recuperação após
restart e histórico, mas acrescentaria complexidade operacional que não era
necessária para validar o ciclo principal.

## O que quebra primeiro em produção?

O primeiro limite é o armazenamento em memória:

- jobs desaparecem quando o processo reinicia;
- o estado não é compartilhado entre réplicas;
- uma réplica diferente não encontra a transcrição criada por outra.

O segundo limite é o consumo de recursos. Vários OCRs simultâneos podem consumir
CPU e memória rapidamente.

O terceiro limite é a retenção. A demonstração não possui um processo automático
de expiração dos PDFs por TTL.

Uma versão de produção precisaria de fila externa, armazenamento privado, banco
compartilhado, limites de concorrência e exclusão automática.

## Onde não confio plenamente?

A menor confiança está nos documentos escaneados ou manuscritos, especialmente
`time-card-04`.

Nesse arquivo, o OCR ainda não recupera dados suficientes. A aplicação responde
com erro explícito em vez de apresentar uma transcrição vazia como concluída.

Também não há gabarito completo para todos os layouts de holerite. A qualidade
medida em `payroll-03` não deve ser generalizada automaticamente para documentos
com estrutura diferente.

Esses casos precisam de mais amostras reais, gabaritos visuais e testes antes de
qualquer uso fora da demonstração.

## Evolução do `payroll-02`

A comparação visual das páginas mostrou dois problemas estruturais:

- referências textuais estavam anexadas à descrição;
- os demonstrativos `MÊS` e `ACERTO` eram misturados.

A correção passou a usar as colunas geométricas da tabela, preservar os dois
blocos e separar os itens do resumo.

Uma tentativa de traduzir as chaves públicas foi revertida ao conferir que o
contrato HTTP era literal. Apenas a interface e os cabeçalhos das planilhas
permaneceram em português-BR.

## Resultado da validação

No estado documentado:

```text
58 passed, 2 skipped
```

Também foram validados:

- `docker compose config`;
- construção completa da imagem;
- inicialização do contêiner;
- `GET /healthz`;
- holerite real;
- cartão de ponto com extração;
- erro honesto no `time-card-04`;
- edição e exportação dos dados corrigidos.

A principal conclusão do processo foi que quantidade de código e quantidade de
testes não substituem decisões corretas de produto. O resultado precisa ser
auditável, revisável e explícito sobre aquilo que a máquina não conseguiu ler.