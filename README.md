# Quick Filler

Aplicação web para transcrição revisável de cartões de ponto e holerites.

## Demonstração

Aplicação publicada: https://quick-filler-desafio-aua5.onrender.com

A interface e os cabeçalhos das planilhas usam português-BR. O JSON e a API
mantêm as chaves literais em inglês exigidas pelo contrato do desafio.

Para executar diretamente no Windows, na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --app-dir backend
```

Para validar:

```powershell
python -m pytest -q
```

```bash
docker compose up --build
```

Depois, abra `http://localhost:8000`.
## Demonstração

Aplicação publicada: https://quick-filler-desafio-aua5.onrender.com

Detalhes técnicos, limitações e política de retenção estão em
[`SOLUCAO.md`](SOLUCAO.md). O registro do desenvolvimento assistido por IA está
em [`PROCESSO.md`](PROCESSO.md).
