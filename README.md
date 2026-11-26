# Data Model Auditor

Aplicativo desktop para Windows que audita modelos de dados exportados pelo Erwin Data Modeler.

Esta versão contém somente a estrutura inicial do repositório. Importação, validação, interface e histórico ainda não foram implementados.

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

## Verificação

Com as dependências de desenvolvimento instaladas:

```text
pytest
ruff check .
mypy src
```
