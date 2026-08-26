# Cobertura de PDFs

Esta matriz registra o comportamento observado da versão de portfólio do Quick Filler.

| Arquivo | Tipo | Texto nativo | Status atual | Evidência / próximo passo |
|---|---|---:|---|---|
| `payroll-01.pdf` | Ficha financeira | 21.390 caracteres | Não suportado no fluxo mensal | Formato acumulado; funcionalidade bônus |
| `payroll-02.pdf` | Holerite | 7.735 caracteres | Testado | Teste real para seções `MÊS` e `ACERTO` |
| `payroll-03.pdf` | Holerite | 4.970 caracteres | Testado | Competência, verbas e bases validadas |
| `payroll-04.pdf` | Holerite | 425 caracteres | Parcial com OCR | Competência, totais e campos por coluna extraídos; revisão manual ainda necessária para erros de OCR |
| `time-card-01.pdf` | Cartão de ponto | 22.589 caracteres | Testado | Páginas e dias extraídos |
| `time-card-02.pdf` | Cartão de ponto | 0 caracteres | Parcial com OCR | OCR executa; avisos de confiabilidade e revisão manual |
| `time-card-03.pdf` | Cartão de ponto | 0 caracteres | Parcial com OCR | Ordem visual das batidas testada no Docker; revisão manual continua necessária |
| `time-card-04.pdf` | Cartão de ponto | 0 caracteres | Não avaliado | Exige OCR; imagem mais difícil |

## Critério de confiabilidade

Uma extração só é considerada confiável quando possui teste automatizado e comparação com referência visual. Resultados parciais de OCR devem ser revisados antes da exportação.