# DATA MODEL AUDITOR

## Instruções oficiais para implementação do projeto

Documento: Especificação de desenvolvimento e execução  
Versão: 1.1  
Linguagem: Python  
Plataforma: Windows Desktop e backend corporativo  
Interface: PySide6  
Arquitetura: Cliente-servidor, Clean Architecture e arquitetura hexagonal  
Gestão: GitHub Issues + GitHub Projects Kanban

A versão 1.1 incorpora o adendo arquitetural de cliente-servidor e multiusuário. Nos pontos de arquitetura, banco, armazenamento, autenticação, concorrência e inteligência artificial, esta versão prevalece sobre a 1.0.

Este documento complementa as diretrizes permanentes em `.cursor/rules/`.

Em caso de conflito, respeite as regras de segurança e as decisões arquiteturais aprovadas pelo responsável pelo projeto. O adendo 1.1 é essa decisão para os aspectos aqui especificados.

## 1. Papel da IA no projeto

Você deverá atuar como:

- Arquiteto de Software Sênior.
- Engenheiro de Software Python.
- Especialista em arquitetura de aplicações desktop.
- Especialista em engenharia de dados.
- Especialista em modelagem de dados.
- Especialista em testes automatizados.
- Responsável pela qualidade técnica do projeto.

Sua responsabilidade é analisar, planejar, implementar, testar e documentar um produto de software profissional.

Não desenvolva o sistema como um protótipo descartável.

O objetivo é criar uma aplicação sustentável, modular, extensível, testável e preparada para utilização em ambiente corporativo.

Todas as decisões deverão respeitar as diretrizes permanentes definidas em `.cursor/rules/`.

## 2. Objetivo do produto

Desenvolver uma solução cliente-servidor para auditoria e validação de modelos de dados exportados pelo Erwin Data Modeler.

O cliente desktop, instalado no Windows, comunica-se exclusivamente com o backend por API REST. O backend interpreta os arquivos, executa as validações e persiste projetos e auditorias em PostgreSQL, compartilhado por vários usuários.

O aplicativo deverá importar um arquivo XML exportado pelo Erwin e confrontar sua estrutura com diferentes documentos de referência.

Documentos utilizados:

- Planilha Excel ou CSV com termos permitidos para nomenclatura.
- Planilha Excel ou CSV com prefixos permitidos.
- Documento PDF com regras de modelagem.
- Documento Word com descrições funcionais das tabelas e campos.

O sistema deverá identificar inconsistências e apresentar os resultados em uma interface gráfica.

O produto será denominado **Data Model Auditor**.

## 3. Requisitos fundamentais

A aplicação deverá atender às seguintes características:

- Cliente desktop no Windows, sem acesso direto ao PostgreSQL.
- Backend central responsável por autenticação, processamento e persistência.
- Banco PostgreSQL compartilhado por múltiplos usuários.
- Permitir múltiplos projetos de auditoria.
- Permitir importação de documentos de referência.
- Permitir substituição e versionamento dos documentos.
- Interpretar XML exportado pelo Erwin Data Modeler 12.x.
- Executar validações automatizadas no backend.
- Apresentar inconsistências em tela.
- Manter histórico de todas as auditorias.
- Comparar auditorias anteriores.
- Preservar os arquivos originais.
- Não modificar automaticamente o XML original.
- Registrar o usuário responsável por auditorias e alterações de regras.

Não implementar dependência obrigatória de serviços externos de IA.

As validações determinísticas deverão continuar funcionando quando o provedor de IA estiver desabilitado ou indisponível. O cliente precisa alcançar o backend; a internet externa não é requisito para o núcleo da auditoria.

## 4. Tecnologias

Utilizar:

- Python 3.12 ou superior.
- PySide6 no cliente desktop.
- FastAPI no backend.
- PostgreSQL como banco central.
- SQLAlchemy 2.x.
- Alembic.
- Pydantic.
- lxml.
- defusedxml.
- pandas.
- openpyxl.
- python-docx.
- PyMuPDF.
- pytest.
- pytest-cov.
- Ruff.
- mypy.
- PyInstaller para o cliente.
- GitHub Actions.

Não utilizar SQLite como banco principal.

Celery e Redis só entram se o volume ou a duração das auditorias justificarem processamento distribuído. Não introduzir essa infraestrutura no MVP.

Verificar a compatibilidade das versões antes de instalar.

Manter as dependências fixadas e documentadas.

## 5. Arquitetura obrigatória

Utilizar arquitetura cliente-servidor, combinada com Clean Architecture e arquitetura hexagonal.

A solução é composta por:

**Desktop Client**

- Python e PySide6.
- Comunicação com o backend somente por API REST.
- Autenticação.
- Interface de gerenciamento.
- Visualização dos resultados.
- Execução das operações pelos serviços do backend.

**Backend**

- Python, FastAPI, SQLAlchemy, Pydantic e Alembic.
- PostgreSQL.
- Autenticação e autorização.
- Gerenciamento de projetos e documentos.
- Processamento de arquivos e interpretação do XML.
- Motor de validação e gestão de regras.
- Histórico e comparação de auditorias.
- Integração opcional com IA.

O domínio e os casos de uso permanecem desacoplados dos frameworks. A comunicação entre cliente e servidor ocorre exclusivamente pelos contratos da API. O cliente desktop não acessa o PostgreSQL.

Separar cada aplicação em:

### Domain

Responsável por:

- Entidades.
- Value Objects.
- Regras de negócio.
- Validadores.
- Contratos.
- Exceções.

### Application

Responsável por:

- Casos de uso.
- Serviços.
- Orquestração.
- DTOs.
- Interfaces de aplicação.

### Infrastructure

Responsável por:

- Persistência.
- Leitura de arquivos.
- XML.
- Excel.
- CSV.
- PDF.
- Word.
- Logs.

### Presentation

No cliente, responsável por:

- Interface PySide6.
- Janelas.
- Widgets.
- Diálogos.
- Tabelas.
- Apresentação dos resultados.

No servidor, a borda externa equivalente é a API REST. Ela não contém regra de negócio.

### Bootstrap

Responsável por:

- Inicialização.
- Configuração.
- Injeção de dependências.

O domínio não poderá depender diretamente de bibliotecas de infraestrutura ou interface gráfica.

## 6. Funcionalidades do sistema

### 6.1 Gerenciamento de projetos

Criar um módulo para gerenciamento dos projetos de auditoria.

Permitir:

- Criar projeto.
- Editar projeto.
- Consultar projeto.
- Consultar arquivos associados.
- Consultar histórico.
- Executar auditoria.
- Comparar auditorias.

Cada projeto deverá possuir identificação própria.

Os arquivos e referências utilizados deverão estar associados ao projeto.

### 6.2 Gerenciamento de documentos de referência

Criar uma área específica para importação e gerenciamento dos documentos.

Categorias:

- XML Erwin.
- Planilha de nomenclatura.
- Planilha de prefixos.
- PDF de regras.
- Word de documentação.

Permitir:

- Importar arquivo.
- Visualizar arquivo importado.
- Identificar nome.
- Identificar extensão.
- Identificar data de importação.
- Identificar versão.
- Identificar hash.
- Substituir arquivo.
- Consultar histórico de versões.

A importação deverá validar a estrutura dos arquivos.

Quando a estrutura não for reconhecida, apresentar uma mensagem clara e permitir o mapeamento das colunas ou estruturas quando aplicável.

Não presumir nomes fixos de colunas nas planilhas.

Criar uma funcionalidade de mapeamento de colunas para associar as colunas reais aos atributos internos do sistema.

### 6.3 Interpretação do XML do Erwin

Implementar um parser específico para XML exportado pelo Erwin Data Modeler 12.x.

Antes de finalizar o parser:

- Solicitar XML real.
- Identificar estrutura, entidades, referências e relacionamentos.
- Documentar os elementos relevantes.
- Criar fixtures e testes de regressão.

Não presumir estrutura de XML baseada apenas em exemplos genéricos. Manter o parser independente do domínio e preparado para futuras versões do Erwin, com leitores específicos quando o formato mudar.

Identificar:

- Estrutura do documento.
- Elementos.
- Atributos.
- Identificadores.
- Relacionamentos.
- Referências internas.
- Propriedades físicas.
- Propriedades lógicas.

Criar uma representação interna independente do formato original.

O modelo interno deverá contemplar:

**Modelo**

- Identificação.
- Nome.
- Descrição.
- Versão, quando disponível.

**Tabela**

- Identificador.
- Nome físico.
- Nome lógico.
- Descrição.
- Subject ou área.
- Campos.

**Campo**

- Identificador.
- Nome físico.
- Nome lógico.
- Descrição.
- Tipo de dado.
- Tamanho.
- Precisão.
- Escala.
- Nulabilidade.
- Default.
- Posição.
- Participação em PK.
- Participação em FK.
- Participação em índices.

**Relacionamentos**

- Tabela de origem.
- Tabela de destino.
- Campos relacionados.
- Cardinalidade.
- Identificação do relacionamento.

**Índices**

- Nome.
- Campos integrantes.
- Tipo.
- Unicidade.
- Outras propriedades disponíveis.

Preservar os identificadores originais quando disponíveis.

Criar testes com XMLs representativos.

Não inventar estruturas que não tenham sido verificadas.

Se houver diferenças entre versões ou formatos de exportação do Erwin, documentar a compatibilidade e implementar leitores específicos quando necessário.

### 6.4 Validação de nomenclatura

Implementar o confronto dos nomes físicos e lógicos com a planilha de termos permitidos e a planilha de prefixos.

A validação deverá considerar:

- Nomenclatura de tabelas.
- Nomenclatura de campos.
- Nome físico.
- Nome lógico.
- Prefixos.
- Termos.
- Ordem dos termos.
- Abreviações.
- Composição do nome.

Exemplo:

`CD_CLIENTE`

O sistema deverá identificar:

- Prefixo: `CD_`.
- Termo: `CLIENTE`.

Verificar se ambos são permitidos.

Exemplos adicionais:

- `NM_CLIENTE`
- `DT_NASCIMENTO`
- `VL_SALDO`
- `ID_CONTA`

Os exemplos são ilustrativos. As regras efetivas deverão ser obtidas das planilhas fornecidas.

O sistema deverá diferenciar regras de nomenclatura física e lógica.

Deverá permitir configurar separadores, composição dos nomes e exceções autorizadas.

A validação deverá ser determinística.

Não utilizar IA para decidir se um nome é válido quando a regra puder ser expressa em código.

### 6.5 Validação de tipos de dados

Implementar validações para:

- Tipo de dado.
- Tamanho.
- Precisão.
- Escala.
- Compatibilidade.
- Nulabilidade.
- Regras específicas por categoria.

O sistema deverá permitir configurar o banco de dados usado como referência da modelagem.

Preparar suporte para:

- Oracle.
- SQL Server.
- PostgreSQL.

Criar uma camada de normalização de tipos.

Não comparar tipos de forma textual sem considerar equivalências e particularidades de cada banco.

As regras deverão ser específicas por banco quando necessário e parametrizadas conforme a documentação de modelagem.

### 6.6 Validação de descrições

Validar:

- Existência da descrição.
- Preenchimento.
- Padrão textual.
- Comprimento, quando estabelecido.
- Clareza.
- Regras de redação.
- Consistência com o nome do campo.
- Consistência com a finalidade documentada.

Separar validações objetivas de avaliações semânticas.

Avaliações semânticas deverão ser identificadas como sugestões ou alertas, quando não houver regra determinística.

### 6.7 Validação de tabelas

Validar:

- Nome físico.
- Nome lógico.
- Prefixo.
- Termos utilizados.
- Descrição.
- Regras de nomenclatura.
- Regras específicas definidas no PDF.

### 6.8 Validação de Primary Key

Validar:

- Existência da PK, quando obrigatória.
- Nomenclatura.
- Composição.
- Campos integrantes.
- Nulabilidade.
- Duplicidade de composição.
- Regras normativas.

### 6.9 Validação de Foreign Key

Validar:

- Existência do relacionamento.
- Campos de origem.
- Campos de destino.
- Compatibilidade dos tipos.
- Nomenclatura.
- Integridade estrutural.
- Regras normativas.

### 6.10 Validação de DEFAULT

Validar:

- Existência quando obrigatória.
- Compatibilidade com o tipo.
- Valor permitido.
- Formatação.
- Regras específicas.

### 6.11 Validação de INDEX

Validar:

- Existência.
- Nomenclatura.
- Composição.
- Campos associados.
- Unicidade.
- Duplicidade.
- Conformidade com as regras de modelagem.

### 6.12 Importação do PDF de regras

O sistema deverá permitir importar documentos PDF.

Implementar:

- Extração de texto.
- Identificação de possíveis regras.
- Classificação das regras.
- Apresentação para revisão.
- Cadastro estruturado.
- Aprovação pelo usuário.
- Versionamento.
- Ativação e desativação.

O PDF deverá ser a fonte normativa.

A IA poderá auxiliar na interpretação, mas não poderá ativar regras automaticamente sem aprovação.

Implementar cadastro manual para regras que não puderem ser extraídas automaticamente.

Considerar OCR como evolução para documentos digitalizados.

### 6.13 Importação e interpretação do Word

Importar documentos DOCX contendo documentação funcional.

Identificar:

- Nome da tabela.
- Nome do campo.
- Nome físico.
- Nome lógico, quando disponível.
- Descrição funcional.

Permitir mapeamento da estrutura do Word.

A aplicação deverá suportar documentos organizados em tabelas e, quando possível, em outros formatos estruturados.

### 6.14 Confronto XML versus Word

Executar obrigatoriamente:

- Identificar campos existentes no XML, mas ausentes no Word.
- Identificar campos existentes no Word, mas ausentes no XML.
- Identificar campos sem descrição.
- Comparar descrições.
- Identificar descrições divergentes.
- Validar descrições conforme os padrões.
- Identificar inconsistências semânticas quando houver mecanismo habilitado.

A associação deverá considerar:

- Nome da tabela.
- Nome físico do campo.
- Identificadores disponíveis.
- Regras de normalização.

Não utilizar somente o nome do campo como chave global, pois diferentes tabelas podem possuir campos com nomes iguais.

Criar regras de normalização para espaços, maiúsculas, acentos e formatação.

Quando houver ambiguidade, não associar registros automaticamente sem sinalizar a situação.

### 6.15 Motor central de validação

Criar um mecanismo independente para executar todas as validações.

Implementar validadores específicos:

- `NamingValidator`
- `PrefixValidator`
- `TableValidator`
- `ColumnValidator`
- `DataTypeValidator`
- `DescriptionValidator`
- `PrimaryKeyValidator`
- `ForeignKeyValidator`
- `DefaultValidator`
- `IndexValidator`
- `RelationshipValidator`
- `DocumentationValidator`

Cada validador deverá possuir contrato comum.

Cada regra deverá possuir:

- Código.
- Nome.
- Categoria.
- Descrição.
- Severidade.
- Condição.
- Mensagem.
- Justificativa.
- Sugestão de correção.
- Fonte normativa.
- Versão.
- Status.

O motor deverá permitir adicionar validadores sem alterar os existentes.

### 6.16 Apresentação das inconsistências

Criar uma tela central de resultados.

Cada inconsistência deverá apresentar:

- Projeto.
- Tabela.
- Campo físico.
- Campo lógico.
- Tipo de validação.
- Código da regra.
- Regra violada.
- Justificativa.
- Sugestão de correção.
- Severidade.
- Fonte normativa.

Utilizar severidades:

- Critical.
- High.
- Medium.
- Low.
- Info.

Permitir filtrar por:

- Projeto.
- Tabela.
- Campo.
- Categoria.
- Severidade.
- Regra.
- Situação.

A primeira versão deverá apresentar resultados em tela.

Não implementar exportação de relatórios como requisito obrigatório do MVP.

Não alterar automaticamente o XML.

### 6.17 Histórico de auditorias

O histórico é obrigatório.

Cada execução deverá registrar:

- Projeto.
- XML utilizado.
- Hash do XML.
- Data e hora.
- Versão das planilhas.
- Versão do PDF.
- Versão do Word.
- Versão das regras.
- Quantidade de inconsistências.
- Resultados completos.

Implementar comparação entre auditorias.

Identificar:

- Inconsistências novas.
- Inconsistências corrigidas.
- Inconsistências persistentes.
- Inconsistências alteradas.

A identificação deverá utilizar uma chave estável baseada no projeto, tabela, campo, regra e contexto aplicável.

Não utilizar apenas o número sequencial da inconsistência.

As auditorias anteriores deverão ser imutáveis.

Alterações posteriores nas regras ou referências não poderão modificar resultados anteriores.

## 7. Interface gráfica

Criar uma aplicação desktop profissional utilizando PySide6.

A interface deverá possuir:

- Dashboard.
- Gerenciamento de projetos.
- Importação de arquivos.
- Gerenciamento de referências.
- Cadastro e aprovação de regras.
- Visualização do modelo importado.
- Execução de auditoria.
- Resultados.
- Detalhamento de inconsistências.
- Histórico.
- Comparação de auditorias.
- Configurações.

Utilizar navegação intuitiva.

Criar tabelas com filtros.

Utilizar indicadores de quantidade de erros por categoria e severidade.

Manter consistência visual.

O processamento da auditoria ocorre no backend. A interface não pode bloquear durante importações e validações.

Acompanhar cada execução com identificador, status, progresso, início, conclusão, erros e resultados.

Utilizar chamadas assíncronas à API. Usar `QThread` apenas para trabalho local que não pertença ao backend, como preparação da interface.

Implementar barra de progresso e tratamento de cancelamento quando seguro.

## 8. Banco de dados

Utilizar PostgreSQL como banco central. Não utilizar SQLite como banco principal.

O banco deverá suportar múltiplos usuários acessando os mesmos projetos e auditorias.

Implementar SQLAlchemy 2.x e Alembic.

Implementar:

- Integridade referencial.
- Transações.
- Controle de concorrência.
- Migrations.
- Índices.
- Backup.
- Recuperação.

Criar entidades para:

- `Project`
- `ImportedFile`
- `ReferenceVersion`
- `NamingTerm`
- `PrefixRule`
- `ModelingRule`
- `DataModel`
- `ModelTable`
- `ModelColumn`
- `ModelRelationship`
- `ModelIndex`
- `AuditExecution`
- `AuditFinding`
- `RuleCategory`
- `AuditFindingComparison`
- Usuários, papéis e histórico de atividades.

Armazenar os resultados históricos de forma imutável.

Auditorias concluídas não podem ser reescritas. Cada execução registra o usuário responsável e o conjunto exato de referências utilizadas.

Os documentos importados ficam em armazenamento central, não como conteúdo grande dentro do PostgreSQL, salvo justificativa técnica registrada. O banco guarda metadados, hash e a referência da versão.

Avaliar versionamento otimista para entidades editáveis.

## 9. Estrutura do projeto

Avaliar monorepo e preservar o que já existe. A estrutura de referência da versão 1.1 é:

```text
data-model-auditor/
  client/
  server/
  shared/
  docs/
    architecture/
    requirements/
    decisions/
    user_manual/
  tests/
    unit/
    integration/
    acceptance/
    fixtures/
  scripts/
  .github/
    workflows/
    ISSUE_TEMPLATE/
  .cursor/
    rules/
```

Dentro de `client/` e de `server/`, manter as camadas:

```text
domain/
application/
infrastructure/
presentation/
bootstrap/
```

No cliente, `presentation/` é a interface PySide6. No servidor, a borda de entrada é a API.

O repositório atual ainda usa `src/data_model_auditor/`. Essa pasta permanece até uma reorganização autorizada. Não apagar nem mover arquivos existentes sem justificativa e autorização.

O domínio compartilhado não importa FastAPI, PySide6, SQLAlchemy nem cliente HTTP.

## 10. Segurança e confiabilidade

Implementar:

- HTTPS.
- Proteção contra XXE.
- Validação de arquivos.
- Limites de tamanho.
- Tratamento de documentos inválidos.
- Tratamento de exceções.
- Logging centralizado.
- Preservação dos arquivos originais.
- Controle de integridade dos arquivos com hash SHA-256.
- Gestão segura de segredos.
- Configurações separadas para desenvolvimento, homologação e produção.
- Backup e restauração.
- PostgreSQL inacessível a partir dos computadores clientes.

Não executar macros.

Não executar código extraído de documentos.

Não utilizar `eval` ou `exec` para interpretar regras.

Não registrar senhas, tokens ou documentos confidenciais nos logs.

As regras deverão ser armazenadas em estruturas de dados controladas e executadas por validadores Python previamente implementados.

As permissões são verificadas no backend. Restrições apenas na interface desktop não são suficientes.

## 11. Histórico de desenvolvimento no GitHub

O projeto já possui um repositório GitHub.

Utilizar exclusivamente o repositório fornecido pelo responsável.

Antes de realizar alterações:

- Analisar estrutura.
- Analisar commits.
- Analisar branches.
- Verificar workflows.
- Verificar Issues.
- Verificar Projects.
- Verificar configurações.

Não apagar histórico ou configurações.

Criar ou configurar GitHub Project com Kanban:

- Backlog.
- Ready.
- In Progress.
- In Review.
- Done.

Criar Issues detalhadas.

Cada Issue deverá conter:

- Título.
- Objetivo.
- Contexto.
- Descrição técnica.
- Critérios de aceite.
- Dependências.
- Prioridade.
- Milestone.
- Labels.

Criar Milestones:

- M0 — Fundação e arquitetura.
- M1 — Interface e projetos.
- M2 — Importação e interpretação.
- M3 — Nomenclatura e motor de regras.
- M4 — Validação estrutural.
- M5 — Documentação Word.
- M6 — Regras PDF.
- M7 — Histórico e auditoria.
- M8 — Testes e distribuição.

### Priorização

**P0:** funcionalidades indispensáveis para o MVP.

**P1:** funcionalidades importantes para completar a primeira versão.

**P2:** funcionalidades evolutivas.

Todas as tarefas deverão estar associadas a um Milestone e ter critérios de aceite.

## 12. Estratégia de implementação

Desenvolver incrementalmente.

Não tentar implementar todo o sistema de uma vez.

### Fase 0 — Análise e planejamento

- Inspecionar repositório.
- Analisar regras do Cursor.
- Elaborar arquitetura.
- Identificar dependências.
- Identificar riscos.
- Criar documentação inicial.
- Criar backlog.
- Configurar Kanban.
- Criar Issues.
- Criar Milestones.
- Priorizar tarefas.

Entregável: planejamento aprovado e backlog estruturado.

### Fase 1 — Fundação

- Configurar ambiente de cliente e servidor.
- Configurar dependências.
- Criar estrutura, preservando o que já existe até a reorganização autorizada.
- Implementar domínio desacoplado.
- Implementar persistência em PostgreSQL.
- Criar migrations.
- Configurar autenticação e papéis iniciais.
- Configurar testes.
- Configurar CI.

Entregável: estrutura funcional e testada, com API e banco central.

### Fase 2 — Interface

- Criar janela principal.
- Criar navegação.
- Criar autenticação no cliente.
- Criar dashboard.
- Criar projetos.
- Criar tela de importação.

Entregável: aplicação desktop inicial, consumindo a API.

### Fase 3 — Importação de arquivos

- Criar parser XML.
- Criar leitores Excel e CSV.
- Criar leitor PDF.
- Criar leitor Word.
- Criar mapeamento de estruturas.
- Criar testes de integração.

Entregável: importação funcional dos documentos.

### Fase 4 — Motor de validação

- Implementar arquitetura dos validadores.
- Implementar nomenclatura.
- Implementar prefixos.
- Implementar tabelas.
- Implementar campos.
- Implementar tipos de dados.
- Implementar descrições.
- Implementar PK.
- Implementar FK.
- Implementar DEFAULT.
- Implementar INDEX.

Entregável: motor de validação funcional.

### Fase 5 — Documentação Word

- Interpretar Word.
- Associar tabelas.
- Associar campos.
- Comparar descrições.
- Identificar campos ausentes.
- Identificar campos sem descrição.
- Criar testes.

Entregável: confronto XML versus Word.

### Fase 6 — PDF e regras normativas

- Extrair texto.
- Identificar regras.
- Permitir revisão.
- Cadastrar regras.
- Versionar regras.
- Ativar e desativar regras.

Entregável: gestão de regras de modelagem.

### Fase 7 — Resultados e histórico

- Criar tela de resultados.
- Criar filtros.
- Criar detalhamento.
- Registrar auditorias.
- Comparar auditorias.
- Identificar evolução.

Entregável: módulo completo de auditoria.

### Fase 8 — Finalização

- Executar testes.
- Corrigir defeitos.
- Revisar arquitetura.
- Atualizar documentação.
- Configurar PyInstaller.
- Gerar executável.
- Criar instalador Windows.
- Criar release.

Entregável: versão instalável do Data Model Auditor.

## 13. Testes e critérios de aceite

Utilizar pytest.

Metas:

- 90% de cobertura no domínio.
- 80% de cobertura geral.

Testar todos os validadores.

Criar testes para arquivos válidos e inválidos.

Criar testes de regressão.

Executar:

```text
pytest
ruff check .
mypy src/
```

Não considerar uma funcionalidade concluída sem executar os testes aplicáveis.

Não criar funções vazias para simular funcionalidades implementadas.

Não utilizar mocks para substituir todos os testes de integração com arquivos reais ou representativos.

Criar também testes para:

- API.
- Autenticação.
- Autorização.
- Permissões.
- Concorrência.
- Persistência compartilhada.
- Upload de arquivos.
- Controle de acesso aos documentos.
- Integração com IA.
- Indisponibilidade do provedor de IA.
- Integridade do histórico.
- Integração entre desktop, backend e banco de dados.

## 14. Distribuição Windows

A aplicação deverá ser distribuída como software desktop.

Utilizar PyInstaller para empacotamento.

Avaliar Inno Setup para criação de instalador.

O instalador do cliente desktop deverá:

- Instalar a aplicação.
- Criar atalhos.
- Guardar configuração local do cliente em diretório de dados do usuário.
- Permitir inicialização pelo menu Iniciar.
- Não sobrescrever a configuração local em atualizações.
- Permitir desinstalação.

Projetos, documentos e auditorias permanecem no backend. Desinstalar o cliente não apaga o banco central.

Testar o executável em ambiente Windows limpo.

## 15. Documentação

Criar e manter:

- `README.md`
- `CHANGELOG.md`
- Arquitetura.
- Requisitos.
- Guia de instalação.
- Guia do usuário.
- Guia de desenvolvimento.
- Documentação do banco.
- Documentação do motor de regras.
- ADRs.

Atualizar a documentação em cada entrega relevante.

## 16. Processo obrigatório de trabalho

Para cada tarefa:

1. Consultar a Issue.
2. Analisar dependências.
3. Verificar regras arquiteturais.
4. Criar ou selecionar branch.
5. Implementar em pequenas alterações.
6. Criar testes.
7. Executar testes.
8. Executar análise estática.
9. Revisar código.
10. Atualizar documentação.
11. Criar Pull Request.
12. Vincular Issue.
13. Aguardar revisão quando aplicável.
14. Atualizar o Kanban.

Uma tarefa somente poderá ser considerada Done quando seus critérios de aceite forem cumpridos.

## 17. Controle de escopo

Não implementar funcionalidades não solicitadas sem registrar a proposta.

Não inventar regras de negócio.

Não inventar estrutura do XML.

Não assumir formatos de planilhas.

Não criar integrações externas obrigatórias.

Não adicionar funcionalidades apenas para tornar a aplicação visualmente mais complexa.

Toda funcionalidade adicional deverá possuir justificativa técnica e prioridade aprovada.

## 18. Primeira execução no Cursor

Ao receber estas instruções, siga esta sequência:

1. Analise o repositório existente.
2. Leia todas as regras em `.cursor/rules/`.
3. Identifique a estrutura atual.
4. Verifique acesso ao GitHub.
5. Verifique as ferramentas disponíveis.
6. Elabore o plano de desenvolvimento.
7. Crie ou atualize a documentação técnica.
8. Crie Issues e Milestones.
9. Configure o Kanban.
10. Classifique todas as tarefas em P0, P1 e P2.
11. Apresente o planejamento.
12. Identifique os bloqueios que dependem de informações ou arquivos do responsável.

Depois da aprovação do planejamento, inicie a implementação P0, seguindo a ordem das dependências.

Não interrompa o desenvolvimento por dúvidas que possam ser resolvidas de forma segura e documentada. Entretanto, não invente decisões sobre formatos de arquivos, regras normativas ou estruturas do Erwin.

Solicite esclarecimento quando uma informação for indispensável.

## 19. Relatório de evolução

Ao finalizar cada etapa, apresentar:

- Etapa concluída.
- Funcionalidades implementadas.
- Issues concluídas.
- Issues pendentes.
- Testes executados.
- Resultado dos testes.
- Cobertura.
- Arquivos criados.
- Decisões arquiteturais.
- Problemas identificados.
- Próxima etapa.

Não afirmar que uma operação foi realizada no GitHub se não houver confirmação da ferramenta.

## 20. Definição de sucesso do projeto

O projeto será considerado concluído quando existir uma aplicação Windows instalada e funcional que permita:

- Criar projetos.
- Importar XML do Erwin.
- Importar planilhas de nomenclatura.
- Importar planilhas de prefixos.
- Importar PDF de regras.
- Importar Word de documentação.
- Interpretar o modelo de dados.
- Executar todas as validações definidas.
- Identificar inconsistências.
- Apresentar justificativas e sugestões.
- Consultar histórico.
- Comparar auditorias.
- Preservar os arquivos originais.
- Manter rastreabilidade das regras utilizadas.
- Executar testes automatizados.
- Ser distribuída por instalador Windows.

O sistema somente será considerado apto para uso corporativo quando também:

- Dois ou mais usuários conseguirem acessar os mesmos projetos.
- Os dados estiverem centralizados.
- As permissões forem verificadas no backend.
- As auditorias identificarem seus executores.
- Os documentos estiverem protegidos.
- O histórico permanecer íntegro.
- A aplicação funcionar sem IA externa.
- A IA puder ser habilitada opcionalmente.
- A indisponibilidade da IA não interromper as validações.
- O cliente desktop não precisar de acesso direto ao banco de dados.

## 21. API

Utilizar FastAPI.

Criar endpoints organizados por domínio:

- Authentication.
- Users.
- Projects.
- Documents.
- References.
- Data Models.
- Rules.
- Audits.
- Findings.
- Audit History.
- AI Analysis.

Utilizar contratos Pydantic.

Documentar a API por OpenAPI.

Implementar versionamento da API.

Implementar tratamento padronizado de erros.

## 22. Autenticação e autorização

Implementar autenticação centralizada.

Preparar integração com OAuth2 e OpenID Connect.

Não armazenar senhas em texto puro.

Utilizar mecanismos seguros de armazenamento de credenciais.

Implementar autorização baseada em papéis (RBAC).

Perfis iniciais:

- Administrator.
- Analyst.
- Viewer.

Todas as operações relevantes deverão registrar o usuário responsável.

Validar permissões no backend.

## 23. Armazenamento de arquivos

Os documentos importados deverão ficar em armazenamento central.

Não armazenar arquivos grandes diretamente no PostgreSQL sem justificativa técnica.

Utilizar uma abstração de armazenamento que permita implementar:

- Sistema de arquivos em servidor.
- Armazenamento de objetos compatível com S3.

Preservar os arquivos originais.

Associar cada documento ao projeto e à sua versão.

Registrar hash SHA-256.

Controlar permissões de acesso.

Implementar política de backup e retenção.

## 24. Inteligência artificial opcional

Implementar uma camada de abstração para provedores de IA.

A integração deverá permitir substituir o provedor sem modificar o domínio.

Utilizar Strategy e Adapter quando apropriado.

A IA poderá apoiar:

- Análise semântica de descrições.
- Identificação de ambiguidades.
- Sugestões de redação.
- Interpretação assistida das regras PDF.

As validações determinísticas deverão permanecer independentes da IA.

A IA não poderá aprovar ou ativar regras normativas automaticamente.

Toda sugestão deverá ser identificada como gerada por IA.

Exigir aprovação humana quando a sugestão alterar regras ou documentos de referência.

Implementar:

- Configuração do provedor.
- Controle de habilitação.
- Gestão segura de credenciais.
- Limites de consumo.
- Tratamento de indisponibilidade.
- Timeout.
- Logging sem exposição de informações sensíveis.
- Controle de dados enviados.

Não enviar documentos completos para provedores externos sem autorização expressa.

Minimizar os dados enviados, utilizando apenas os trechos necessários para a análise.

O sistema deverá continuar funcionando integralmente sem provedor de IA.

## 25. Multiusuário e concorrência

Implementar:

- Cadastro de usuários.
- Autenticação.
- Perfis.
- Permissões.
- Histórico de atividades.
- Identificação do autor das auditorias.
- Identificação do autor das alterações de regras.
- Controle de concorrência.
- Proteção contra alterações simultâneas.

Auditorias deverão registrar o usuário responsável e o conjunto exato de referências utilizadas.

As auditorias concluídas deverão ser imutáveis.

Utilizar transações no banco.

Avaliar versionamento otimista para entidades editáveis.

## Princípio final

Desenvolva um produto de engenharia de software, não apenas um conjunto de scripts Python.

Priorize arquitetura, qualidade, rastreabilidade, segurança, manutenibilidade e confiabilidade dos resultados.

A aplicação deverá permitir que as regras de governança de dados evoluam sem exigir alterações constantes no núcleo do sistema.
