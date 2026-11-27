# DATA MODEL AUDITOR

## ESPECIFICAÇÃO DE IMPLEMENTAÇÃO — PRIMEIRA VERSÃO (MVP V1)

Versão: 1.0

Objetivo: Desenvolver a primeira versão funcional do Data Model Auditor, com foco exclusivo na análise de modelos de dados exportados pelo Erwin Data Modeler 12.x.

## 1. DIRETRIZ PRINCIPAL

A partir desta versão, o escopo do projeto deverá ser simplificado.

O objetivo é entregar uma aplicação desktop capaz de:

- Importar XML exportado pelo Erwin.
- Identificar as Subject Areas.
- Exigir a seleção de uma Subject Area.
- Permitir selecionar tabelas e campos específicos.
- Importar documentos de referência.
- Carregar regras de validação.
- Executar auditoria.
- Apresentar inconsistências.
- Gerar relatórios.

O sistema deverá funcionar localmente na máquina do usuário.

### IMPORTANTE

Deixar fora do escopo da primeira versão:

- Login.
- Cadastro de usuários.
- Controle de permissões.
- PostgreSQL.
- SQLite.
- Qualquer banco de dados.
- Backend.
- API REST.
- Comunicação cliente-servidor.
- Persistência de auditorias.
- Histórico centralizado.
- Integração multiusuário.
- Infraestrutura em nuvem.

Não desenvolver essas funcionalidades neste momento.

Não criar tabelas de banco de dados.

Não implementar ORM.

Não criar dependência de servidor externo.

A arquitetura deverá permitir que esses recursos sejam adicionados futuramente sem reconstruir o núcleo da aplicação.

## 2. PRESERVAÇÃO DO CÓDIGO EXISTENTE

Antes de iniciar:

- Inspecionar o repositório.
- Verificar o Git.
- Identificar o estado do Pull Request #28.
- Verificar a branch `feature/reference-readers`.
- Identificar os leitores já desenvolvidos.
- Identificar os contratos existentes.
- Identificar o motor de validação.
- Executar os testes existentes.

Reaproveitar os componentes existentes sempre que possível.

Não recriar:

- Leitor de thesaurus.
- Leitor SM077.
- Leitor PDF.
- Contratos de severidade.
- Contratos de resultado.
- Motor de validação.

Adaptar somente o necessário para execução local.

Não descartar alterações existentes.

## 3. ARQUITETURA DA APLICAÇÃO

Utilizar:

- Python.
- PySide6.
- pytest.
- Pydantic.
- PyYAML.
- Pandas, quando necessário.
- openpyxl para Excel.
- Biblioteca de geração de PDF.
- PyInstaller.
- Inno Setup.

Adotar arquitetura em camadas.

Estrutura de referência:

```text
data-model-auditor/
  src/
    data_model_auditor/
      domain/
      application/
      infrastructure/
      presentation/
      reporting/
      parsers/
      validators/
      references/
      configuration/
      main.py
  rules/
    default_rules.yaml
  references/
    examples/
  tests/
    unit/
    integration/
    fixtures/
  docs/
  scripts/
```

Não modificar a estrutura atual sem antes verificar se ela já possui organização equivalente.

## 4.1 PADRÕES DE PROJETO

Utilizar padrões conhecidos e adequados ao problema:

- Strategy: diferentes validadores.
- Factory: criação de validadores.
- Adapter: integração dos leitores existentes.
- Repository: acesso abstrato a arquivos e referências, sem banco de dados.
- Dependency Injection: composição dos componentes.
- Facade: orquestração da auditoria.

Não utilizar padrões apenas por formalidade.

Manter o domínio independente do PySide6.

## 5. IMPORTAÇÃO DO XML ERWIN

O XML exportado pelo Erwin Data Modeler 12.x será o documento principal da auditoria.

O parser deverá:

- Ler o arquivo XML.
- Identificar Subject Areas.
- Identificar tabelas.
- Identificar campos.
- Identificar nomes físicos.
- Identificar nomes lógicos.
- Identificar descrições.
- Identificar tipos de dados.
- Identificar tamanhos.
- Identificar precisão.
- Identificar escala.
- Identificar nulabilidade.
- Identificar PK.
- Identificar FK.
- Identificar defaults.
- Identificar índices.
- Identificar relacionamentos.

Criar uma representação interna independente do formato XML.

Não misturar interpretação XML com regras de validação.

### 5.1 XML real obrigatório para validação definitiva

Solicitar XML real exportado pelo Erwin Data Modeler 12.x.

Não inventar estruturas XML.

Não considerar o parser concluído antes de validar o comportamento com um XML real.

Criar testes com fixtures representativas.

## 6. SELEÇÃO OBRIGATÓRIA DA SUBJECT AREA

A seleção da Subject Area será obrigatória.

O fluxo deverá ser:

1. Usuário importa XML.
2. Sistema interpreta o XML.
3. Sistema identifica as Subject Areas disponíveis.
4. Sistema apresenta as opções.
5. Usuário seleciona uma Subject Area.
6. Sistema habilita a configuração das tabelas e campos.
7. Sistema permite executar a auditoria.

Não permitir execução sem Subject Area selecionada.

Se o XML não possuir Subject Areas identificáveis:

- Apresentar mensagem clara.
- Não assumir automaticamente uma área.
- Registrar a limitação.
- Orientar o usuário.

A seleção deverá determinar quais tabelas e campos participarão da auditoria.

## 7. SELEÇÃO OPCIONAL DE TABELAS E CAMPOS

Depois de selecionar a Subject Area, apresentar a lista de tabelas.

Permitir:

- Selecionar todas as tabelas.
- Selecionar tabelas individualmente.
- Pesquisar pelo nome físico.
- Pesquisar pelo nome lógico.
- Expandir tabelas.
- Visualizar campos.
- Selecionar campos individualmente.

A seleção de tabelas e campos será opcional.

Comportamento padrão:

- Nenhuma tabela selecionada explicitamente: considerar todas as tabelas da Subject Area.
- Nenhum campo selecionado explicitamente: considerar todos os campos das tabelas incluídas.
- Tabelas selecionadas: considerar somente as tabelas selecionadas.
- Campos selecionados: considerar somente os campos selecionados, respeitando as tabelas selecionadas.

A seleção de campos não deverá eliminar silenciosamente a necessidade de verificar integridade estrutural.

Regras de PK, FK, índices e relacionamentos poderão precisar analisar elementos relacionados fora da seleção explícita.

Quando isso acontecer, o sistema deverá distinguir:

- Elementos auditados.
- Elementos consultados apenas como dependência estrutural.

A interface deverá informar claramente o escopo escolhido.

## 8. IMPORTAÇÃO DOS DOCUMENTOS DE REFERÊNCIA

Permitir importação de:

- Planilha de thesaurus.
- Planilha de prefixos.
- Documento SM077.
- Documento PDF com regras de modelagem.
- Arquivo de regras YAML.

Os leitores já desenvolvidos deverão ser reaproveitados.

Cada documento deverá ser validado na importação.

Apresentar:

- Nome do arquivo.
- Tipo de documento.
- Resultado da leitura.
- Quantidade de registros identificados.
- Erros.
- Avisos.

Não iniciar auditoria quando faltar uma referência obrigatória para as regras habilitadas.

Permitir desabilitar regras que dependam de documentos não fornecidos, desde que essa decisão seja explícita e apresentada no relatório.

## 9. ARQUIVO EXTERNO DE REGRAS

As regras deverão ficar em arquivo texto externo.

Utilizar YAML.

Arquivo padrão:

`rules/default_rules.yaml`

O sistema deverá:

- Carregar o arquivo.
- Validar sua estrutura.
- Informar erros de configuração.
- Permitir edição.
- Permitir selecionar outro arquivo.
- Permitir habilitar ou desabilitar categorias.
- Permitir definir severidade.
- Permitir identificar a origem normativa.

Não codificar as regras diretamente na interface.

Não exigir alteração do código Python para modificar parâmetros de regras.

As regras aprovadas e sua versão deverão ser identificadas em cada execução.

### 9.1 Regras do PDF

O leitor de PDF deverá continuar funcionando.

As regras extraídas do PDF deverão ser apresentadas para revisão.

Fluxo:

Extração → Revisão → Aprovação → Configuração YAML → Ativação.

Não ativar automaticamente regras extraídas.

## 10. VALIDAÇÕES OBRIGATÓRIAS

Implementar e integrar os validadores ao motor existente.

### 10.1 Nomenclatura

Validar:

- Nome físico da tabela.
- Nome lógico da tabela.
- Nome físico do campo.
- Nome lógico do campo.

Verificar se os nomes são compostos por termos válidos do thesaurus.

Considerar:

- Termos existentes.
- Termos inexistentes.
- Abreviações.
- Composição.
- Separadores.
- Ordem dos termos.
- Padrões de escrita.

### 10.2 Prefixos

Validar prefixos conforme planilha de referência.

Considerar categoria do objeto e regras aplicáveis.

### 10.3 Estrutura das tabelas

Validar nomes, convenções e regras aplicáveis às tabelas.

### 10.4 Chaves primárias

Validar:

- Existência quando obrigatória.
- Nomenclatura.
- Tipo de dado.
- Nulabilidade.
- Composição.
- Regras específicas do documento normativo.

### 10.5 Chaves estrangeiras

Validar:

- Existência.
- Relacionamento.
- Compatibilidade de tipos.
- Integridade referencial.
- Nomenclatura.

### 10.6 Tipos de dados

Validar:

- Tipo.
- Tamanho.
- Precisão.
- Escala.
- Nulabilidade.
- Compatibilidade com o banco de destino selecionado.

O banco de destino deverá ser configurável.

Diferenciar o banco de destino do modelo do armazenamento utilizado pela aplicação.

### 10.7 DEFAULT

Validar:

- Existência quando obrigatória.
- Compatibilidade com o tipo.
- Padrão permitido.
- Regras específicas da modelagem.

### 10.8 INDEX

Validar:

- Nomenclatura.
- Existência.
- Composição.
- Regras para índices únicos.
- Regras de índices associados a chaves.

### 10.9 Descrições

Validar:

- Campo sem descrição.
- Descrição insuficiente.
- Descrição incompatível com o padrão.
- Divergência com o SM077.
- Campo documentado e inexistente no XML.
- Campo existente no XML e não documentado no SM077.

## 11. MOTOR DE AUDITORIA

A auditoria deverá receber:

- Modelo normalizado.
- Subject Area.
- Seleção de tabelas.
- Seleção de campos.
- Referências.
- Configuração YAML.
- Banco de destino.

O resultado deverá conter todas as inconsistências identificadas.

Cada inconsistência deverá apresentar:

- Nome da Subject Area.
- Nome da tabela.
- Nome físico do campo.
- Nome lógico do campo.
- Tipo de validação.
- Código da regra.
- Regra violada.
- Justificativa.
- Sugestão de correção.
- Severidade.
- Documento de origem.
- Página ou referência normativa, quando disponível.

Preservar os contratos de resultado e severidade já existentes.

## 12. INTERFACE DESKTOP

Utilizar PySide6.

Criar interface simples, profissional e intuitiva.

### Tela 1 — Início

Apresentar:

- Abrir nova auditoria.
- Importar modelo.
- Configurar referências.
- Configurar regras.

### Tela 2 — Importação

Permitir selecionar o XML.

Apresentar informações do modelo importado.

### Tela 3 — Subject Area

Exigir seleção da Subject Area.

Não permitir avançar sem seleção.

### Tela 4 — Seleção do escopo

Apresentar tabelas e campos.

Permitir seleção opcional.

### Tela 5 — Referências

Permitir importar thesaurus, prefixos, SM077, PDF e YAML.

Apresentar situação dos documentos.

### Tela 6 — Configuração

Permitir selecionar banco de destino.

Permitir revisar regras habilitadas.

### Tela 7 — Execução

Apresentar:

- Escopo da auditoria.
- Regras aplicadas.
- Progresso.
- Resultado da execução.

### Tela 8 — Resultado

Apresentar:

- Total de tabelas analisadas.
- Total de campos analisados.
- Total de regras executadas.
- Total de inconsistências.
- Quantidade por severidade.

Permitir filtrar:

- Subject Area.
- Tabela.
- Campo.
- Categoria.
- Severidade.

### Tela 9 — Detalhamento

Exibir todas as informações da inconsistência.

Permitir visualizar a sugestão de correção e a referência normativa.

## 13. RELATÓRIOS

Gerar relatórios em:

- Excel (`.xlsx`).
- PDF.

O relatório deverá conter:

- Identificação da auditoria.
- Nome do arquivo XML.
- Subject Area selecionada.
- Tabelas incluídas.
- Campos incluídos.
- Banco de destino.
- Documentos de referência utilizados.
- Versão das regras.
- Data e hora.
- Resumo executivo.
- Estatísticas.
- Inconsistências detalhadas.

O relatório deverá preservar a severidade e a justificativa.

No Excel, criar abas:

- Resumo.
- Inconsistências.
- Tabelas.
- Campos.
- Configuração.

Permitir escolher o diretório de exportação.

## 14. EXECUÇÃO LOCAL E AUSÊNCIA DE BANCO

A aplicação deverá funcionar sem conexão com a internet.

Não utilizar banco de dados.

Não exigir servidor.

Não exigir login.

Não persistir auditorias em banco.

Os arquivos originais não deverão ser alterados.

A aplicação poderá manter arquivos temporários durante o processamento.

A única persistência gerada nesta versão deverá ser aquela explicitamente solicitada pelo usuário, como relatórios exportados e arquivos de configuração.

Não criar histórico automático em banco ou arquivos ocultos.

## 15. TESTES

Preservar testes existentes.

Utilizar pytest.

Criar testes unitários e de integração para:

- Parser XML.
- Subject Areas.
- Seleção de tabelas.
- Seleção de campos.
- Leitores de referência.
- YAML.
- Nomenclatura.
- Prefixos.
- PK.
- FK.
- Tipos.
- DEFAULT.
- INDEX.
- Descrições.
- Motor de auditoria.
- Geração Excel.
- Geração PDF.

Criar testes específicos garantindo que a seleção de uma Subject Area não inclua tabelas de outras áreas indevidamente.

Testar também dependências estruturais entre tabelas e campos.

## 16. INSTALADOR

Gerar aplicação instalável para Windows.

Utilizar:

- PyInstaller.
- Inno Setup.

O instalador deverá incluir os componentes necessários para funcionamento local.

Não exigir instalação de Python pelo usuário final.

Incluir:

- Executável.
- Recursos da interface.
- Arquivo de regras padrão.
- Documentação básica.
- Dependências necessárias.

Permitir atualização futura.

Testar instalação, execução e desinstalação.

## 17. CRITÉRIOS DE ACEITE DO MVP

A primeira versão somente será considerada funcional quando:

- O usuário conseguir importar XML real do Erwin 12.x.
- O sistema identificar Subject Areas.
- A seleção da Subject Area for obrigatória.
- O usuário conseguir selecionar tabelas opcionalmente.
- O usuário conseguir selecionar campos opcionalmente.
- Os leitores de referência funcionarem.
- As regras puderem ser carregadas por YAML.
- O sistema validar nomenclatura.
- O sistema validar prefixos.
- O sistema validar PK e FK.
- O sistema validar tipos.
- O sistema validar DEFAULT e INDEX.
- O sistema comparar descrições com SM077.
- As inconsistências apresentarem justificativa e severidade.
- O sistema gerar Excel.
- O sistema gerar PDF.
- A aplicação funcionar sem banco de dados.
- A aplicação funcionar sem login.
- O instalador Windows funcionar em máquina de teste.

## 18. ESTRATÉGIA DE DESENVOLVIMENTO

Priorizar:

### P0

- Preservação do código existente.
- Leitores.
- Parser Erwin.
- Subject Area.
- Seleção de escopo.
- Motor de validação.
- Regras essenciais.
- Relatório.

### P1

- Interface refinada.
- Configuração avançada de regras.
- Interpretação e aprovação das regras PDF.
- Melhorias dos relatórios.

### P2

- IA semântica.
- Histórico persistente.
- Login.
- Banco central.
- Multiusuário.
- Backend.
- Integração corporativa.

Não desenvolver itens P1 e P2 antes de entregar o núcleo funcional P0, salvo dependências técnicas justificadas.

## 19. RELATÓRIO DE DESENVOLVIMENTO

Ao concluir cada etapa, apresentar:

- Componentes reaproveitados.
- Componentes implementados.
- Arquivos modificados.
- Testes executados.
- Resultado dos testes.
- Commits.
- Pull Requests.
- Pendências.
- Próximas tarefas.

Não declarar funcionalidades concluídas sem testes.

## 20. DIRETRIZ FINAL

O Data Model Auditor V1 deverá ser uma ferramenta desktop de auditoria de modelos de dados.

Seu objetivo é analisar, identificar e documentar inconsistências.

A prioridade é entregar valor funcional rapidamente, com arquitetura organizada e possibilidade de evolução futura.

Não implementar login, banco de dados ou backend nesta versão.

Concentrar todos os esforços no parser Erwin, seleção da Subject Area, comparação documental, motor de validação e geração de relatórios.
