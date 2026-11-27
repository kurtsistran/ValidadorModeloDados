# ADR 0001 — Arquitetura cliente-servidor

Data: 2026-11-26
Status: aceita

## Contexto

A primeira especificação tratava o Data Model Auditor como um aplicativo desktop com SQLite local. A versão 1.1 passou a exigir vários usuários, banco central, permissão verificada no servidor e inteligência artificial opcional.

O repositório ainda contém um único pacote, `src/data_model_auditor`. A divisão em `client/`, `server/` e `shared/` está definida, mas ainda não foi autorizada como movimentação dos arquivos existentes.

## Decisão

A solução é cliente-servidor:

- O cliente desktop usa PySide6 e conversa com o backend somente por HTTPS e API REST.
- O backend usa FastAPI. Autenticação, autorização, auditoria e leitura de arquivos acontecem nele.
- PostgreSQL é o banco principal. SQLite não será usado para os dados compartilhados.
- Os documentos originais ficam em armazenamento central, fora das linhas do banco, com hash SHA-256.
- A IA generativa entra por uma porta substituível. A validação determinística funciona sem provedor.
- Até a reorganização autorizada, o código permanece em `src/data_model_auditor`, com as camadas `domain`, `application`, `infrastructure`, `presentation` e `bootstrap`.
- A borda HTTP fica em `infrastructure/http` e é composta por `bootstrap`. Ela não recebe regra de negócio. A interface PySide6 continua em `presentation`.

## Consequências

O cliente não recebe credencial nem acesso direto ao PostgreSQL. Celery, Redis e armazenamento compatível com S3 ficam fora do MVP. O parser do Erwin e os importadores de planilha, PDF e Word só serão implementados com amostras reais.
