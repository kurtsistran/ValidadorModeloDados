# Data Model Auditor

Solução cliente-servidor para auditar modelos exportados pelo Erwin Data Modeler 12.x.

O cliente desktop falará com o backend somente pela API. Esta entrega contém a decisão de arquitetura, a configuração por ambiente, os contratos de severidade e perfil, o motor de validação e a casca HTTP. Ainda não há parser, interface gráfica, autenticação nem persistência.

A decisão está em `docs/decisions/0001-client-server-architecture.md`.

## Estrutura

```text
src/data_model_auditor/
  domain/            conceitos e contratos, sem framework
  application/       casos de uso
  infrastructure/    adaptadores, persistência e leitura de arquivos
  presentation/      interface PySide6
  bootstrap/         composição das dependências
tests/
  unit/
  integration/
  acceptance/
  fixtures/
docs/
```

## Requisitos

- Python 3.12 ou superior

## Configuração

Copie `.env.example` para `.env` se quiser alterar os valores locais. Segredos não entram no Git.

- `APP_ENV`: `development`, `homologation` ou `production`
- `API_HOST`
- `API_PORT`
- `LOG_LEVEL`

## API

```text
uvicorn data_model_auditor.bootstrap.api:app --reload
```

A saúde da API fica em `GET /api/v1/health`.

## Verificação

Com as dependências de desenvolvimento instaladas:

```text
pytest
ruff check .
mypy src
```
