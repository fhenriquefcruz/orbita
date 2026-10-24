# ORBITA 3.0 — PROMPT MESTRE DE ENGENHARIA, DESIGN E IMPLEMENTAÇÃO

## Contrato de execução integral para evolução de uma assessoria pessoal inteligente

**Projeto:** ORBITA — Assessoria Pessoal Inteligente  
**Repositório oficial:** https://github.com/fhenriquefcruz/orbita  
**Aplicação publicada:** https://fhenriquefcruz.github.io/orbita/  
**Versão de referência:** 2.2 — confirmar no repositório  
**Versão-alvo:** 3.0  
**Idioma principal:** Português brasileiro (pt-BR)  
**Abordagem:** Mobile-first, produto funcional, arquitetura sustentável, experiência premium e evolução incremental  
**Prioridade:** Qualidade real e verificável acima de velocidade aparente de entrega.

---

# PARTE I — CONTRATO DE EXECUÇÃO

## 1. MISSÃO PRINCIPAL

Você atuará como uma equipe multidisciplinar sênior responsável pela evolução completa do ORBITA.

Assuma simultaneamente as competências de:

- Product Manager e Product Owner.
- Especialista em experiência do usuário (UX).
- Especialista em interface e design de produto (UI).
- Engenheiro de software sênior.
- Arquiteto de aplicações web.
- Especialista em aplicações mobile-first.
- Especialista em acessibilidade digital.
- Engenheiro de qualidade e testes.
- Especialista em segurança de aplicações.
- Especialista em integrações e automações.
- Especialista em Progressive Web Apps (PWA).
- Especialista em DevOps, GitHub Actions e publicação.

Essas competências devem orientar decisões técnicas concretas. Não devem resultar apenas em justificativas teóricas.

Sua missão é transformar o ORBITA em uma aplicação pessoal digital madura, confiável, visualmente refinada e funcionalmente integrada.

**O resultado não deve parecer um protótipo, uma demonstração de interface ou um painel administrativo genérico. Deve parecer um produto digital completo.**

O usuário deve conseguir organizar compromissos, tarefas, ideias, projetos, decisões e informações importantes com o menor esforço possível.

O sistema deve ajudá-lo a compreender sua rotina, recuperar informações e tomar decisões melhores.

A complexidade deve estar na engenharia. A simplicidade deve estar na experiência.

## 2. REGRAS INEGOCIÁVEIS

Estas regras têm precedência sobre qualquer preferência estética ou implementação secundária.

**R01 — Implementação real**

Não confunda documentação, planejamento, prototipação e implementação. Uma funcionalidade somente pode receber o status de concluída quando seu comportamento tiver sido implementado e validado.

**R02 — Preservação do produto**

Não reconstrua indiscriminadamente o projeto. Analise a implementação existente, preserve suas capacidades úteis e mantenha compatibilidade com os dados já armazenados.

**R03 — Nenhum botão fictício**

Todo elemento interativo precisa executar a ação que anuncia. Quando uma ação depender de infraestrutura ainda inexistente, não apresente o recurso como operacional.

**R04 — Integridade dos dados**

Nenhuma alteração visual ou arquitetural justifica perda, corrupção, duplicação ou descarte silencioso de dados existentes.

**R05 — Responsividade obrigatória**

A interface deverá ser projetada para celulares desde o início e adaptada aos demais dispositivos. Não será aceita uma versão desktop simplesmente comprimida.

**R06 — Segurança por arquitetura**

Nunca exponha credenciais, tokens, dados privados ou segredos em código executado no navegador ou em repositório público.

**R07 — Inteligência transparente**

Não simule recursos de IA generativa, pesquisa externa, agendamento automático, sincronização ou envio de mensagens que não estejam tecnicamente operacionais.

**R08 — Qualidade verificável**

Não declare que uma tela, integração ou jornada funciona sem apresentar evidência correspondente.

**R09 — Evolução integral**

Execute todas as fases previstas que forem tecnicamente viáveis no ambiente disponível. Não interrompa o trabalho apenas porque a primeira fase ficou visualmente satisfatória.

**R10 — Limitações explícitas**

Quando houver impedimento técnico, ausência de acesso, dependência externa ou operação não verificável, identifique precisamente o problema e forneça o caminho necessário para resolvê-lo.

**R11 — Sem regressões silenciosas**

Uma melhoria nova não poderá inutilizar funcionalidades existentes. Execute verificações de regressão após mudanças relevantes.

**R12 — Nenhuma conclusão presumida**

Não preencha checklists automaticamente e não trate a ausência de erros visíveis como evidência de funcionamento correto.

## 3. PROCEDIMENTO OBRIGATÓRIO DE EXECUÇÃO

Siga este fluxo:

1. Inspecionar o repositório e a aplicação publicada.
2. Identificar a arquitetura, as funcionalidades e suas dependências.
3. Registrar uma linha de base técnica e funcional.
4. Classificar componentes existentes em manter, melhorar, reorganizar ou remover.
5. Construir uma matriz de requisitos e testes.
6. Definir o design system e a arquitetura de navegação.
7. Implementar as alterações em incrementos coerentes.
8. Testar cada incremento.
9. Corrigir regressões e inconsistências.
10. Consolidar a interface e os fluxos entre módulos.
11. Executar testes integrados.
12. Validar responsividade, acessibilidade, segurança e persistência.
13. Publicar a versão quando houver acesso e condições adequadas.
14. Verificar o resultado publicado.
15. Produzir um relatório técnico e funcional com evidências.

**Importante:** o planejamento é uma etapa, não o produto final. Após a auditoria, prossiga diretamente à implementação.

Evite interrupções para aprovações estéticas rotineiras. Utilize as diretrizes estabelecidas e tome decisões justificadas.

Não execute operações destrutivas irreversíveis sem as salvaguardas e confirmações necessárias.

---

# PARTE II — DEFINIÇÃO DO PRODUTO

## 4. PROPÓSITO DO ORBITA

O ORBITA é uma assessoria pessoal inteligente centrada na organização da vida cotidiana, no acompanhamento de responsabilidades e na recuperação contextual de informações.

Ele deve atuar sobre seis necessidades fundamentais:

### 4.1 Capturar

Permitir que o usuário registre rapidamente algo que não pode esquecer.

### 4.2 Organizar

Transformar informações dispersas em registros coerentes, classificados e recuperáveis.

### 4.3 Priorizar

Distinguir assuntos realmente relevantes de informações que podem aguardar.

### 4.4 Acompanhar

Evidenciar tarefas abertas, compromissos próximos, projetos e assuntos dependentes de terceiros.

### 4.5 Recuperar

Facilitar consultas sobre decisões, histórico e informações registradas anteriormente.

### 4.6 Assistir

Oferecer assistência conversacional e funcional por meio de Vânia e dos especialistas, respeitando as capacidades disponíveis.

## 5. OBJETIVOS DE EXPERIÊNCIA

O usuário deve conseguir:

- Compreender suas principais prioridades em poucos segundos.
- Criar um registro simples sem navegar por vários formulários.
- Localizar um registro conhecido com facilidade.
- Consultar e atualizar pendências sem reconstruir seu contexto.
- Identificar visualmente urgências, atrasos e próximos compromissos.
- Conversar com Vânia e confirmar ações sugeridas.
- Acessar suas informações também sem conexão, nas funções locais compatíveis.
- Identificar claramente se os dados estão salvos localmente ou sincronizados.

**Meta de produto:** reduzir esforço cognitivo, quantidade de interações desnecessárias e tempo gasto para encontrar e atualizar informações.

As metas de tempo devem ser medidas em testes de usabilidade, não presumidas por aparência.

## 6. PRINCÍPIOS DE DESIGN DO PRODUTO

Aplique os seguintes princípios em todas as telas:

1. Clareza antes de quantidade.
2. Utilidade antes de decoração.
3. Hierarquia antes de diversidade cromática.
4. Reconhecimento antes de memorização.
5. Consistência antes de originalidade desnecessária.
6. Ação contextual antes de navegação excessiva.
7. Feedback antes de suposição.
8. Prevenção de erros antes de mensagens corretivas.
9. Transparência antes de aparência de inteligência.
10. Sofisticação discreta antes de efeitos visuais chamativos.

Um recurso avançado não precisa estar permanentemente exposto para ser facilmente acessível.

---

# PARTE III — AUDITORIA E DIAGNÓSTICO

## 7. AUDITORIA DO REPOSITÓRIO

Antes de qualquer alteração significativa, examine:

- Arquitetura HTML, CSS e JavaScript.
- Dependências e ferramentas de build.
- Organização de diretórios.
- Inicialização e montagem da interface.
- Sistema de navegação e roteamento.
- Componentes reutilizáveis.
- Camadas de domínio e persistência.
- Funcionamento das conversas com Vânia.
- Regras e responsabilidades dos especialistas.
- Mecanismo de prioridades.
- Construção de resumos.
- Tratamento de datas e horários.
- Exportação e importação de dados.
- Estrutura do bot Telegram.
- Configuração de GitHub Pages.
- Workflows de publicação.
- Manifest, service worker e estratégias de cache.
- Estados offline e conectividade.
- Testes existentes.
- Acessibilidade e navegação por teclado.
- Tratamento de erros.
- Vulnerabilidades evidentes.
- Histórico recente das alterações relevantes.

Não assuma que a descrição da versão anterior corresponde perfeitamente ao estado atual do código.

Verifique.

## 8. INVENTÁRIO FUNCIONAL

Construa uma tabela com os campos:

| Campo | Finalidade |
|---|---|
| Identificador | Código rastreável do requisito |
| Módulo | Área funcional correspondente |
| Funcionalidade | Comportamento esperado |
| Estado atual | Implementado, parcial, demonstrativo ou ausente |
| Decisão | Manter, melhorar, reorganizar ou remover |
| Prioridade | P0, P1, P2 ou P3 de implementação |
| Dependências | Requisitos anteriores |
| Teste | Como verificar |
| Resultado | Aprovado, reprovado, bloqueado ou não testado |

Utilize identificadores como `ORB-FUN-001`, `ORB-UX-001`, `ORB-DATA-001` e `ORB-SEC-001`.

A classificação deve ser mantida atualizada durante a execução.

## 9. ANÁLISE DE RISCOS

Identifique especialmente:

- Mudanças que possam afetar dados locais existentes.
- Alterações de schema sem migração.
- Conflitos entre módulos que utilizam os mesmos registros.
- Inconsistência de filtros e contadores.
- Erros de data decorrentes de fuso horário.
- Problemas de navegação em dispositivos móveis.
- Service workers servindo versões antigas.
- Erros de base path na publicação.
- Interfaces que aparentam integração sem possuir backend.
- Exposição acidental de segredos.
- Dependências frágeis ou abandonadas.

Para riscos significativos, registre impacto, probabilidade, mitigação e forma de recuperação.

---

# PARTE IV — DIREÇÃO CRIATIVA E DESIGN SYSTEM

## 10. IDENTIDADE VISUAL

### 10.1 Conceito criativo

**ORBITA — Inteligência discreta. Organização sofisticada. Tecnologia humana.**

A experiência deve combinar:

- Elegância de software premium.
- Clareza de uma ferramenta de produtividade.
- Naturalidade de um assistente pessoal.
- Consistência de um sistema profissional.
- Sensação de tranquilidade e controle.

O design precisa ser reconhecível sem exageros.

Não utilizar estética de ficção científica, painéis neon, brilhos artificiais, excesso de gradientes ou elementos decorativos que dificultem a leitura.

A qualidade visual deverá vir de composição, proporção, tipografia, espaçamento, contraste e refinamento das interações.

### 10.2 Paleta cromática principal

| Token | Hexadecimal | Finalidade |
|---|---|---|
| Background | `#0B1216` | Fundo da aplicação |
| Surface | `#121D23` | Superfícies principais |
| Surface Elevated | `#192831` | Elementos elevados |
| Border | `#30434A` | Separações |
| Text Primary | `#EDF5F3` | Texto principal |
| Text Secondary | `#91A5A7` | Informações secundárias |
| Accent Primary | `#69D3B1` | Identidade e ação primária |
| Accent Info | `#88B9E8` | Programação e informação |
| Accent Warning | `#E6B665` | Atenção |
| Accent Danger | `#F08282` | Erros e criticidade |
| Accent Creative | `#B7A0ED` | Ideias e criatividade |

Esses valores são pontos de partida e podem receber ajustes técnicos para assegurar contraste e harmonia.

Crie tokens semânticos adicionais para:

- Texto desabilitado.
- Placeholder.
- Hover.
- Pressed.
- Focus ring.
- Seleção ativa.
- Fundo de informação.
- Fundo de sucesso.
- Fundo de aviso.
- Fundo de erro.
- Divisórias.
- Sobreposição de modal.
- Sombras.
- Controles de formulário.
- Estados offline.
- Badges de prioridade.

Evite espalhar cores diretamente pelo código.

### 10.3 Aplicação inteligente das cores

Cor deve ter função, não apenas presença.

A página inicial pode usar acentos verdes e azuis; atrasos e riscos devem receber cores específicas; ideias podem utilizar violeta.

Não use todas as cores em todas as seções.

Não aplique fundos coloridos saturados em vários cards simultaneamente.

Evite transformar todos os elementos importantes em verde, pois isso elimina a hierarquia.

Não use vermelho em situações comuns.

O significado de uma cor deverá permanecer consistente entre telas.

### 10.4 Tipografia

Utilize uma família como Inter ou Manrope, preferencialmente com estratégia de carregamento eficiente e fallback apropriado.

Construa uma escala responsiva de títulos e textos.

Diretrizes iniciais:

| Elemento | Referência |
|---|---|
| Título principal | 28–38 px |
| Título de seção | 20–24 px |
| Título de card | 15–18 px |
| Texto principal | 14–16 px |
| Informação auxiliar | 12–14 px |
| Contadores | 24–32 px |

Não utilize tamanhos menores para acomodar excesso de conteúdo.

Mantenha altura de linha confortável, pesos consistentes e largura de texto apropriada.

Evite excesso de caixa alta e espaçamento artificial entre letras.

### 10.5 Espaçamento e geometria

Adote uma escala baseada em múltiplos de 4 px.

Tokens sugeridos:

`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64`

Raios de referência:

- Cards: 14–18 px.
- Botões: 10–12 px.
- Campos: 10–12 px.
- Modais: 16–20 px.
- Badges: formato compacto ou arredondado.

Padronize alturas, margens, alinhamentos e paddings.

A interface deve possuir ritmo visual consistente.

Espaçamento não pode ser usado para esconder falta de estrutura.

### 10.6 Iconografia

Selecione uma única família de ícones, como Lucide.

Estabeleça espessura de traço, tamanhos, alinhamento e estados.

Use ícones que tenham significado reconhecível.

Não misture emojis, ícones preenchidos e ícones de contorno sem necessidade.

Ícones não substituem rótulos quando a ação não é universalmente evidente.

### 10.7 Elevação e profundidade

Utilize sombras e elevação com moderação.

Prefira separação por:

1. Espaçamento.
2. Diferenças discretas de superfície.
3. Bordas suaves.
4. Hierarquia tipográfica.
5. Sombras somente quando necessárias.

Evite cards dentro de cards e camadas visuais excessivas.

---

# PARTE V — ARQUITETURA DE NAVEGAÇÃO

## 11. ESTRUTURA PRINCIPAL

A aplicação será organizada em seis contextos principais:

**Início**  
Central de prioridades, situação atual e ações rápidas.

**Vânia**  
Assistência conversacional, interpretação de demandas e execução confirmada de ações.

**Registros**  
Organização e manutenção de tarefas, compromissos, projetos, ideias, decisões e informações.

**Resumos**  
Sínteses objetivas da rotina e consultas históricas.

**Minha equipe**  
Especialistas, responsabilidades e capacidades.

**Configurações**  
Preferências, políticas, integrações, privacidade, dados e informações operacionais.

A navegação deve possuir um modelo consistente de estado ativo, histórico e retorno.

## 12. DESKTOP

Utilize sidebar lateral:

- Expandida em aproximadamente 220–240 px.
- Recolhida em aproximadamente 64–76 px.
- Marca ORBITA no topo.
- Itens organizados em uma única hierarquia.
- Destaque claro do destino ativo.
- Tooltip nos ícones da versão recolhida.
- Indicador operacional discreto.
- Configurações na região inferior, quando apropriado.

A área principal deverá possuir largura máxima confortável e distribuição por grid.

Evite ocupação excessiva das laterais.

Não estique formulários e textos por toda a largura de monitores grandes.

## 13. MOBILE

Implementar navegação inferior com cinco destinos:

**Início | Vânia | Registros | Resumos | Mais**

O menu Mais dará acesso à equipe, configurações e funcionalidades secundárias.

A navegação deve:

- Respeitar a safe area do iPhone.
- Permanecer facilmente acessível.
- Evitar sobreposição com o conteúdo.
- Identificar claramente a seção ativa.
- Não disputar espaço com múltiplos menus.
- Adaptar-se ao teclado virtual.
- Preservar contexto quando apropriado.

A interface não deve exigir gestos ocultos para funcionalidades essenciais.

Não deve haver controles que funcionem apenas com hover.

## 14. REGRAS DE NAVEGAÇÃO E CONTEXTO

Implemente, conforme o comportamento da arquitetura escolhida:

- Retorno previsível.
- Navegação por histórico.
- Preservação apropriada de filtros.
- Preservação de rascunhos em situações críticas.
- Estados de carregamento.
- Identificação de página atual.
- Tratamento de rotas desconhecidas.
- Foco acessível após mudança de contexto.
- Proteção contra perda acidental de edição.

Ao sair de um registro detalhado, o usuário deve conseguir retornar à lista sem perder desnecessariamente sua busca ou filtro.

---

# PARTE VI — ESPECIFICAÇÃO DAS TELAS

## 15. INÍCIO — CENTRAL DE DECISÕES

A página inicial deve responder:

**O que exige minha atenção e o que devo fazer agora?**

### 15.1 Cabeçalho contextual

Exibir saudação curta, associada ao período local configurado.

Exemplo:

"Bom dia. Estas são suas prioridades."

Complementar com um resumo baseado em dados reais.

Não usar números artificiais.

Ações principais:

- Novo registro.
- Conversar com Vânia.

Evitar hero banners desnecessários.

### 15.2 Indicadores acionáveis

Apresentar quatro perspectivas:

| Indicador | Comportamento |
|---|---|
| Para hoje | Abre registros relevantes do dia |
| Em atraso | Abre registros vencidos ainda pendentes |
| Aguardando retorno | Abre dependências externas |
| Próximos prazos | Abre compromissos futuros relevantes |

Cada indicador deve:

- Utilizar contagem real.
- Aplicar critérios documentados.
- Ser clicável.
- Abrir o filtro correspondente.
- Atualizar após mudanças nos registros.
- Distinguir ausência de dados de erro de carregamento.

Não permitir contadores provenientes de uma base de dados diferente da listagem exibida.

### 15.3 Seu foco agora

Apresentar até três registros prioritários.

Critérios de seleção:

1. Urgência confirmada.
2. Prazos vencidos.
3. Compromissos próximos.
4. Prioridade elevada.
5. Dependências que exigem acompanhamento.

A ordenação deve ser determinística e documentada, utilizando desempate estável.

Cada item poderá oferecer ações como:

- Abrir.
- Atualizar.
- Reagendar.
- Concluir.

Ações de mudança devem produzir feedback e atualização imediata das demais visualizações.

### 15.4 Captura rápida

Implementar o campo:

"O que você precisa lembrar, resolver ou desenvolver?"

A entrada poderá sugerir:

- Título.
- Tipo de registro.
- Prazo.
- Prioridade.
- Especialista.
- Informações adicionais.

A interpretação deverá respeitar as capacidades disponíveis.

Se houver somente regras locais, utilizar regras locais explicitamente identificadas.

Antes de salvar, apresentar uma prévia editável.

Nunca criar um registro silenciosamente apenas porque o usuário escreveu uma frase.

### 15.5 Síntese de Vânia

Criar um bloco compacto contendo, quando existirem dados:

- Observação mais relevante.
- Eventual risco.
- Próxima ação sugerida.
- Acesso ao resumo completo.

Evitar repetição dos mesmos contadores do dashboard.

### 15.6 Estados especiais

Preparar a tela para:

- Primeiro acesso.
- Nenhum registro.
- Dia sem compromissos.
- Existência exclusiva de registros concluídos.
- Falha de leitura.
- Dados antigos exigindo migração.
- Modo offline.
- Alterações ainda não persistidas.

Nenhum estado deve resultar em interface quebrada ou espaço vazio inexplicável.

## 16. VÂNIA — ASSISTÊNCIA CONVERSACIONAL

A conversa deve ser uma das experiências mais refinadas do sistema.

### 16.1 Estrutura

A tela deve conter:

- Identificação de Vânia.
- Modo operacional real.
- Histórico de mensagens.
- Campo de composição.
- Botão de envio.
- Estados de processamento.
- Respostas com ações contextuais.
- Tratamento de erros.
- Mensagens de orientação quando necessário.

No mobile, o layout deve priorizar a conversa.

O campo de entrada deve permanecer utilizável com o teclado aberto, respeitando o comportamento real do Safari e Android.

### 16.2 Mensagens

Distinguir visualmente:

- Mensagens do usuário.
- Respostas de Vânia.
- Informação do sistema.
- Ações sugeridas.
- Falhas de processamento.
- Confirmações.

Preservar ordem cronológica e comportamento de rolagem.

Não rolar automaticamente para o final quando o usuário estiver consultando mensagens anteriores, salvo comportamento explicitamente adequado.

### 16.3 Sugestões contextuais

No estado inicial:

- Organizar meu dia.
- Ver prioridades.
- Registrar compromisso.
- Consultar pendências.

Após o início da conversa, reduzir sugestões persistentes que ocupem espaço.

### 16.4 Respostas estruturadas

Vânia deverá apresentar ações estruturadas quando houver informação suficiente.

Exemplo:

**Possível compromisso identificado**

- Título: Reunião de acompanhamento.
- Data: 27/10/2026.
- Especialista: Zezé.
- Prioridade: Normal.

Ações:

**Confirmar registro | Editar | Cancelar**

A confirmação deve acionar um fluxo real de persistência e refletir nos demais módulos.

Não se limitar a adicionar visualmente um card na conversa.

### 16.5 Transparência da inteligência

Estabelecer modos reais:

- Assistência local.
- IA conectada e disponível.
- Processando.
- Indisponível.
- Aguardando confirmação.

Somente apresentar o modo de IA conectada quando houver um provedor efetivamente integrado, autenticação adequada e funcionamento verificável.

Não fabricar respostas externas ou citações.

### 16.6 Segurança da conversa

Conteúdo introduzido pelo usuário, recuperado de registros ou recebido futuramente de integrações deve ser tratado como dado, e não como autorização automática para executar operações.

Ações que modificam registros devem utilizar validação e confirmação.

Operações externas sensíveis deverão seguir políticas adicionais de autorização.

### 16.7 Histórico

Garantir que o histórico esteja organizado e que seu comportamento de persistência seja claro.

Não induzir o usuário a acreditar que o histórico está sincronizado entre aparelhos se for salvo apenas no navegador.

## 17. MINHA EQUIPE — ESPECIALISTAS

Preservar integralmente as identidades funcionais:

| Especialista | Responsabilidade |
|---|---|
| Vânia | Coordenação e interpretação geral |
| Zezé | Agenda, tarefas e compromissos |
| Gusttavo Lima | Criatividade e ideias |
| Bastião | Memória profissional |
| Obina | Riscos e antecipação |
| Chicão | Projetos e execução |
| Fátima | Pesquisa e verificação |

Os especialistas são componentes funcionais e não representações reais de pessoas.

### 17.1 Apresentação visual

Vânia deve receber maior destaque hierárquico.

Os demais especialistas devem ter cards compactos, contendo:

- Nome.
- Função.
- Breve descrição.
- Exemplos de demandas.
- Estado da capacidade disponível.
- Ação contextual funcional.

Aplique identidade cromática discreta para diferenciar responsabilidades.

Não transformar o módulo em uma coleção excessiva de avatares, ornamentos e efeitos.

### 17.2 Comportamento

O usuário deve conseguir compreender:

- Quando um especialista é acionado.
- Qual sua responsabilidade.
- Que informações utiliza.
- Qual ação está sugerindo.
- Quais limitações possui.

O roteamento entre especialistas deve ser implementado e testado.

Não afirmar que um especialista realizou pesquisa externa sem que isso tenha ocorrido.

## 18. REGISTROS — CENTRAL DE ORGANIZAÇÃO

### 18.1 Estrutura

Implementar:

- Cabeçalho compacto.
- Total de registros conforme o contexto.
- Ação Novo registro.
- Busca instantânea.
- Filtros essenciais.
- Filtros avançados recolhíveis.
- Ordenação.
- Listagem.
- Visualização detalhada.
- Edição contextual.

Filtros principais:

**Tudo | Abertos | Hoje | Em atraso | Concluídos**

Filtros avançados:

- Tipo.
- Situação.
- Prioridade.
- Área.
- Especialista.
- Período.
- Responsável, quando aplicável.

### 18.2 Busca

A busca deve:

- Considerar os campos definidos como pesquisáveis.
- Tratar letras maiúsculas e minúsculas adequadamente.
- Ter normalização de acentos quando apropriado.
- Apresentar estado sem resultados.
- Funcionar em conjunto com filtros.
- Permitir limpar a expressão pesquisada.
- Não apagar dados ou alterar registros.

### 18.3 Listagem

Desktop: apresentação em lista compacta e organizada.

Mobile: cards compactos com hierarquia adaptada.

Mostrar prioritariamente:

- Título.
- Tipo.
- Situação.
- Prazo, quando relevante.
- Prioridade.
- Responsável, quando útil.

Evitar exibir todos os metadados em cada linha.

### 18.4 Ordenação

Permitir:

- Maior urgência.
- Prazo mais próximo.
- Atualização mais recente.
- Criação mais recente.
- Prioridade.

A ordenação deve ser estável e previsível.

### 18.5 Detalhamento

Ao abrir um registro, oferecer:

- Visualização completa.
- Edição.
- Alteração de prioridade.
- Alteração de situação.
- Reagendamento.
- Conclusão.
- Arquivamento.
- Exclusão confirmada.
- Histórico de alterações disponível.

No desktop, utilizar painel lateral quando apropriado.

No mobile, utilizar uma apresentação que não comprima excessivamente o conteúdo.

### 18.6 Atualização entre módulos

Uma alteração em qualquer registro deverá refletir coerentemente:

- Nos indicadores da tela inicial.
- Nos filtros.
- Na área de foco.
- Nos resumos.
- Nas consultas de Vânia.
- Nos alertas.
- Nas demais visualizações dependentes.

**Não desenvolver fontes de verdade independentes para cada tela.**

## 19. NOVO REGISTRO — FORMULÁRIO INTELIGENTE

### 19.1 Princípio

O formulário deve ser completo em capacidade e simples na primeira apresentação.

### 19.2 Campos principais

- Título.
- Natureza do registro.
- Descrição ou contexto.
- Prazo ou data, quando aplicável.
- Prioridade.
- Situação.

### 19.3 Detalhes adicionais

Exibir mediante expansão ou conforme o contexto:

- Área.
- Especialista.
- Origem.
- Confiabilidade.
- Sensibilidade.
- Acompanhamento.
- Relações com outros registros.
- Responsável externo.
- Datas de criação e atualização, em modo informativo.
- Histórico.

### 19.4 Adaptação por natureza

**Tarefa:** ação, prazo, prioridade e situação.

**Compromisso:** data, horário, contexto e situação.

**Projeto:** objetivo, andamento, responsabilidades e informações associadas.

**Ideia:** conteúdo, contexto, classificação e possibilidade de desenvolvimento.

**Decisão:** decisão tomada, motivação, origem e data.

**Pendência:** assunto, responsável externo, situação e acompanhamento.

**Informação:** conteúdo e contexto de recuperação.

Campos irrelevantes não devem ser obrigatórios por padrão.

### 19.5 Datas e horários

Todos os campos de data devem permitir seleção por calendário.

Testar especificamente:

- Safari no iPhone.
- Chrome no Android.
- Navegadores desktop.
- Entrada com teclado.
- Seleção por toque.
- Limpeza de data.
- Alteração de horário.

Datas puras devem ser tratadas diferentemente de instantes com horário e fuso.

Evite erros de um dia decorrentes de conversões automáticas de UTC.

Armazene horários e fusos de forma coerente e documentada.

### 19.6 Validação

Implementar:

- Identificação de obrigatoriedade.
- Mensagem contextual de erro.
- Preservação de valores.
- Controle contra submissão duplicada.
- Confirmação de salvamento.
- Proteção contra perda acidental.
- Mensagem clara em falha de persistência.
- Retorno seguro à tela anterior.

Não classificar automaticamente informação como verificada apenas porque foi cadastrada.

## 20. RESUMOS — INFORMAÇÃO QUE GERA AÇÃO

### 20.1 Resumo matinal

Título sugerido:

**Seu dia em perspectiva**

Apresentar:

1. Compromissos do dia.
2. Três prioridades relevantes.
3. Pendências críticas.
4. Riscos identificados.
5. Próxima ação sugerida.

Não exibir categorias vazias sem utilidade.

### 20.2 Resumo vespertino

Título sugerido:

**Fechamento do dia**

Apresentar:

1. Atividades concluídas no dia.
2. Demandas ainda abertas.
3. Assuntos aguardando terceiros.
4. Itens relevantes para amanhã.
5. Recomendações de continuidade.

Não confundir registros historicamente concluídos com registros efetivamente concluídos na data do resumo.

### 20.3 Recursos

- Alternância manhã/tarde.
- Consulta por data.
- Atualização da prévia.
- Cópia de conteúdo.
- Data de geração.
- Origem dos dados.
- Estados vazios.
- Identificação de limitações operacionais.

Resumos automáticos e agendados somente podem ser apresentados como ativos após implementação e verificação real.

## 21. CONFIGURAÇÕES

Organizar as configurações por grupos:

**Preferências**
- Idioma.
- Fuso horário.
- Aparência, quando disponível.
- Preferências de exibição.

**Notificações e alertas**
- Política de prioridade.
- Horários previstos.
- Silêncio protegido.
- Canais operacionais.

**Dados**
- Exportação.
- Importação.
- Política de armazenamento.
- Informações de versão.
- Recuperação e integridade.

**Integrações**
- Telegram.
- Serviços externos realmente conectados.
- Estado de conectividade e autenticação.
- Recursos disponíveis e indisponíveis.

**Privacidade e segurança**
- Limitações do armazenamento local.
- Tratamento das informações.
- Operações sensíveis.
- Orientações sobre backup.

**Sobre o ORBITA**
- Versão.
- Informações operacionais.
- Histórico de atualizações relevante.

Não transformar todas essas opções em destinos de navegação principal.

---

# PARTE VII — COMPONENTES DE INTERFACE

## 22. BIBLIOTECA VISUAL OBRIGATÓRIA

Padronizar componentes reutilizáveis para:

- Botões.
- Campos de texto.
- Textareas.
- Selects.
- Calendários.
- Badges.
- Cards.
- Indicadores.
- Tabs.
- Menus.
- Dropdowns.
- Modais.
- Painéis laterais.
- Listas.
- Alertas.
- Toasts.
- Skeletons.
- Estados vazios.
- Estados de erro.
- Indicadores de processamento.
- Controles de confirmação.
- Componentes de conversa.

Evite componentes genéricos excessivamente configuráveis e difíceis de manter.

## 23. CONTRATO DE INTERAÇÃO

Cada controle deve possuir comportamento definido para:

| Estado | Exigência |
|---|---|
| Normal | Finalidade compreensível |
| Hover | Feedback apropriado em dispositivos compatíveis |
| Focus | Destaque acessível |
| Pressed | Resposta visual |
| Loading | Impedir operações duplicadas quando necessário |
| Disabled | Estado e motivo coerentes |
| Success | Confirmação apropriada |
| Error | Mensagem e recuperação |
| Empty | Orientação contextual |

Um controle visual não pode estar ativo se não existe um comportamento implementado.

## 24. MICROINTERAÇÕES

Aplicar transições discretas, preferencialmente rápidas e consistentes.

Evitar:

- Animações prolongadas.
- Movimentos desnecessários.
- Efeitos de brilho.
- Alterações de layout durante carregamento.
- Toasts em excesso.
- Feedback que desapareça antes da leitura.

Respeitar `prefers-reduced-motion`.

Animações nunca devem bloquear a ação do usuário.

## 25. MICROCOPY E LINGUAGEM

Toda a interface deve utilizar português brasileiro natural.

Preferir:

- "Novo registro" em vez de terminologia excessivamente técnica.
- "Aguardando retorno" quando representar uma pendência externa.
- "Salvar alterações" quando houver edição.
- "Não foi possível salvar" quando a gravação falhar.

Evitar:

- Frases motivacionais repetitivas.
- Mensagens artificiais de entusiasmo.
- Linguagem excessivamente corporativa.
- Descrições técnicas nos locais errados.
- Mensagens de erro sem orientação.
- Afirmações exageradas sobre a inteligência do sistema.

Textos de interface devem ser curtos, consistentes e orientados à ação.

---

# PARTE VIII — RESPONSIVIDADE E EXPERIÊNCIA MOBILE

## 26. ESTRATÉGIA MOBILE-FIRST

Desenvolver primeiramente a organização da informação para telas pequenas.

Depois ampliar progressivamente para tablet e desktop.

Não esconder funcionalidades essenciais apenas porque a tela ficou menor.

Redesenhe a organização de cada módulo conforme o contexto.

### 26.1 Matriz obrigatória de larguras

| Largura | Verificação |
|---|---|
| 320 px | Celulares compactos |
| 360 px | Android compacto |
| 390 px | iPhone de referência |
| 428 px | Celulares largos |
| 768 px | Tablet vertical |
| 1024 px | Tablet horizontal/notebook |
| 1440 px | Desktop |
| 1920 px | Monitor amplo |

Os valores são cenários de teste, não necessariamente breakpoints rígidos.

Os breakpoints devem refletir necessidades reais do conteúdo.

### 26.2 Requisitos obrigatórios

- Nenhuma rolagem horizontal acidental.
- Nenhum texto importante cortado.
- Nenhum botão inacessível.
- Nenhuma sobreposição de cards.
- Nenhum modal maior que a área utilizável sem possibilidade de navegação.
- Nenhum conteúdo oculto pela navegação inferior.
- Nenhum input inutilizável com teclado aberto.
- Nenhuma dependência exclusiva de hover.
- Nenhuma perda de contexto causada pela reorganização.
- Nenhuma tabela compactada até ficar ilegível.

Áreas de toque devem buscar dimensão mínima de 44 × 44 px.

### 26.3 Comportamento do teclado virtual

Validar:

- Entrada de texto na conversa.
- Formulários longos.
- Modais.
- Campos próximos ao rodapé.
- Rolagem para campo em foco.
- Barra inferior.
- Botões de confirmação.

Não confiar apenas em emulação de viewport para validar todos os comportamentos do Safari real.

Quando teste em dispositivo físico não estiver disponível, registrar essa limitação.

### 26.4 Safe areas

Aplicar suporte correto a áreas seguras e barras de navegação do sistema operacional.

Evitar posicionamento absoluto frágil que cause sobreposição em iPhones.

---

# PARTE IX — ACESSIBILIDADE

## 27. PADRÃO DE ACESSIBILIDADE

Adotar WCAG 2.2 nível AA como referência para desenvolvimento e validação.

Requisitos:

- Semântica HTML apropriada.
- Títulos em hierarquia lógica.
- Labels associados a campos.
- Controles acessíveis pelo teclado.
- Foco visível.
- Ordem de foco consistente.
- Contraste suficiente.
- Mensagens de erro identificáveis.
- Feedback anunciado a tecnologias assistivas.
- Suporte a leitores de tela.
- Estados não dependentes exclusivamente de cor.
- Diálogos com gestão adequada de foco.
- Possibilidade de fechar diálogos.
- Alternativas a gestos complexos.
- Respeito à redução de movimento.
- Conteúdo utilizável com zoom.

Utilize como referências mínimas:

- Contraste de texto comum: 4,5:1.
- Contraste de texto grande: 3:1.
- Contraste de componentes e indicadores relevantes: 3:1, quando aplicável.

Execute auditoria automatizada e verificações manuais.

Uma pontuação automatizada não substitui testes de navegação real e tecnologias assistivas.

---

# PARTE X — REGRAS DE NEGÓCIO

## 28. PRIORIDADES

Preservar o modelo:

| Código | Significado | Tratamento |
|---|---|---|
| P0 | Crítica | Urgência confirmada |
| P1 | Alta | Atenção prioritária |
| P2 | Normal | Acompanhamento habitual |
| P3 | Baixa | Acompanhamento oportuno |

Diferenciar obrigatoriamente:

- Prioridade.
- Urgência.
- Prazo.
- Situação.
- Confiabilidade.
- Sensibilidade.

Não elevar automaticamente uma tarefa a P0 apenas porque seu prazo venceu.

Evitar interpretações arbitrárias.

## 29. SITUAÇÕES OPERACIONAIS

Padronizar:

- A fazer.
- Programada.
- Em execução.
- Aguardando terceiros.
- Bloqueada.
- Concluída.
- Cancelada.
- Arquivada.

Definir transições válidas e seus efeitos.

Exemplo: concluir um registro deve atualizar o estado, registrar o momento da conclusão e recalcular indicadores dependentes.

Não considerar concluído um registro apenas porque sua data passou.

## 30. POLÍTICA DE ALERTAS

Preservar como configuração de referência:

- Resumo matinal: 07h30.
- Resumo vespertino: 18h.
- Silêncio protegido: 20h às 07h30.

Esses horários não representam, por si só, agendamentos operacionais.

Para alertas efetivos fora do navegador aberto, será necessária uma arquitetura compatível com execução agendada e canal de entrega real.

Regras:

- Agrupar alertas repetidos.
- Evitar notificações sem utilidade.
- Priorizar assuntos confirmados.
- Respeitar silêncio protegido.
- Permitir consultar o registro de origem.
- Não inventar urgência.
- Distinguir alertas locais de mensagens efetivamente enviadas.

## 31. COERÊNCIA TEMPORAL

Definir regras de negócio para:

- Registros vencidos.
- Registros de hoje.
- Próximos compromissos.
- Conclusões do dia.
- Acompanhamentos futuros.
- Registros sem prazo.
- Fuso horário.
- Datas históricas.

Testar virada de dia, mês e ano.

Distinguir corretamente um compromisso com hora definida de um registro que possui apenas data.

---

# PARTE XI — DADOS, PERSISTÊNCIA E INTEGRIDADE

## 32. FONTE ÚNICA DE VERDADE

A aplicação deve possuir uma camada de domínio e persistência coerente.

Evitar duplicar registros entre dashboard, conversa, listagens e resumos.

Todos os módulos deverão consultar e atualizar dados a partir de contratos compartilhados.

Mudanças relevantes precisam propagar atualizações de forma previsível.

## 33. MODELO DE DADOS

Auditar o modelo existente antes de propor mudanças.

Preservar, quando existentes:

- Identificador estável.
- Tipo.
- Título.
- Descrição.
- Situação.
- Prioridade.
- Datas.
- Origem.
- Especialista.
- Confiabilidade.
- Sensibilidade.
- Relações.
- Histórico de alterações.
- Versão de schema.

Documentar campos obrigatórios, opcionais, valores aceitos e defaults.

Não inventar propriedades complexas que não possuam finalidade concreta.

## 34. ESTRATÉGIA DE MIGRAÇÃO

Toda mudança incompatível no armazenamento deverá contemplar:

1. Identificação da versão anterior.
2. Leitura validada.
3. Preservação de dados desconhecidos quando seguro.
4. Conversão explícita.
5. Verificação da consistência.
6. Tratamento de falhas.
7. Prevenção de migração duplicada.
8. Estratégia de recuperação.
9. Testes com dados legados.
10. Registro da versão resultante.

Nunca apagar dados antigos sem validação da conversão.

Considere que o GitHub Pages não possui acesso direto ao armazenamento local do navegador do usuário. A migração precisa funcionar no próprio cliente ou por outro mecanismo seguro efetivamente implementado.

## 35. PERSISTÊNCIA

Preserve a operação local existente.

Caso seja necessário adotar IndexedDB ou outra tecnologia, apresente a justificativa e implemente migração segura.

Tratar:

- Armazenamento vazio.
- Conteúdo inválido.
- Quota excedida.
- Falhas de leitura.
- Falhas de gravação.
- Dados legados.
- Atualização interrompida.
- Abas simultâneas, quando aplicável.
- Registros duplicados.
- Mudanças incompletas.

Não afirmar que dados foram salvos quando a operação falhar.

## 36. IMPORTAÇÃO E EXPORTAÇÃO

Implementar fluxo profissional de backup.

### Exportação

- JSON estruturado.
- Versão identificada.
- Data de exportação.
- Nome previsível de arquivo.
- Formato documentado.
- Tratamento de erros.
- Nenhum envio externo não autorizado.

### Importação

- Seleção de arquivo.
- Validação.
- Prévia.
- Identificação de quantidades.
- Avisos de incompatibilidade.
- Detecção de duplicidades.
- Escolha entre mesclar e substituir.
- Confirmação antes de substituir.
- Backup preventivo quando aplicável.
- Importação segura.
- Resultado verificável.

Não considerar uma importação concluída apenas porque o arquivo foi selecionado.

## 37. RASTREABILIDADE

Registros devem manter informações suficientes para distinguir:

- Criação.
- Alteração.
- Conclusão.
- Cancelamento.
- Arquivamento.
- Origem da informação.

A rastreabilidade deve ser proporcional à arquitetura disponível.

Não simular auditoria imutável ou histórico distribuído quando houver somente armazenamento local editável.

---

# PARTE XII — SEGURANÇA E PRIVACIDADE

## 38. SEGURANÇA DO FRONT-END

O GitHub Pages é um ambiente de hospedagem estática.

Não tratar código público como backend privado.

Proibido incorporar:

- Token do Telegram.
- Credenciais.
- Senhas.
- Segredos de API.
- Chaves privadas.
- Dados pessoais exportados.
- Arquivos de configuração com informações sensíveis.

Revisar também histórico Git, workflows, artefatos de build e variáveis publicadas inadvertidamente.

## 39. PROTEÇÕES OBRIGATÓRIAS

Implementar práticas apropriadas de:

- Validação de dados.
- Escapamento seguro.
- Prevenção de XSS.
- Renderização sem HTML não confiável.
- Controle de dependências.
- Gestão segura de erros.
- Não divulgação de informações sensíveis.
- Verificação de operações destrutivas.
- Proteção contra duplicação de comandos.
- Tratamento de dados importados como não confiáveis.

Caso seja introduzido um backend, realizar avaliação específica de autenticação, autorização, controle de acesso, rate limiting, armazenamento seguro de segredos e segurança das APIs.

## 40. PRIVACIDADE

A interface deve comunicar de forma objetiva:

- Onde os dados estão armazenados.
- Se existe sincronização.
- Se há envio a serviços externos.
- Quais integrações estão ativas.
- O que acontece ao limpar dados do navegador.
- Como gerar backup.

Avisos detalhados pertencem preferencialmente a Configurações.

Não repetir grandes alertas em todas as telas.

---

# PARTE XIII — ARQUITETURA TÉCNICA

## 41. DIRETRIZ ARQUITETURAL

Não limitar o redesign a mudanças de CSS.

Organizar responsabilidades de maneira modular, proporcional ao tamanho do projeto.

Separar, quando justificável:

- Inicialização.
- Navegação.
- Componentes visuais.
- Estado.
- Domínio.
- Persistência.
- Validações.
- Regras de prioridades.
- Conversas.
- Resumos.
- Integrações.
- Tratamento de erros.
- Testes.

Não adotar framework novo apenas por preferência pessoal.

Avaliar o custo de migração antes de qualquer decisão arquitetural.

## 42. CONTRATOS ENTRE CAMADAS

A interface não deve manipular diretamente estruturas de armazenamento em vários pontos desconectados.

Centralize operações de domínio com funções testáveis.

Exemplos conceituais:

- Criar registro.
- Atualizar registro.
- Concluir registro.
- Buscar registros.
- Aplicar filtros.
- Calcular prioridades.
- Gerar resumo.
- Exportar backup.
- Importar backup.

Garanta tratamento uniforme de erros e validações.

## 43. GERENCIAMENTO DE ESTADO

Manter coerência entre:

- Registros.
- Dashboard.
- Conversa.
- Resumos.
- Alertas.
- Configurações.

Não depender de recarregamento manual da página para refletir uma edição recém-concluída.

Evitar estados derivados duplicados que se tornem inconsistentes.

## 44. PWA

Preservar e aprimorar:

- Manifest válido.
- Ícones apropriados.
- Instalabilidade.
- Service worker.
- Cache versionado.
- Offline compatível.
- Atualização de versão.
- Tratamento de recursos indisponíveis.

Testar especialmente a atualização entre versões.

Não permitir que o service worker mantenha indefinidamente uma interface antiga.

Não armazenar respostas privadas ou credenciais em cache público.

## 45. TELEGRAM E BACKEND

Preservar o código existente do bot.

Validar a arquitetura atual antes de modificá-la.

A aplicação web e o Telegram poderão possuir armazenamentos separados.

Não apresentar sincronização real até que exista infraestrutura para isso.

Uma integração completa deverá considerar:

- Backend autenticado.
- API segura.
- Persistência compartilhada.
- Identificação do proprietário.
- Controle de permissões.
- Credenciais protegidas.
- Agendamento confiável.
- Monitoramento.
- Tratamento de erros.
- Confirmação de ações sensíveis.

Quando a infraestrutura não existir, preservar uma fronteira arquitetural clara para sua futura implementação.

Não construir uma integração visual fictícia.

---

# PARTE XIV — DESEMPENHO E CONFIABILIDADE

## 46. REQUISITOS DE PERFORMANCE

Projetar a aplicação para carregamento ágil e interação fluida.

Utilizar as métricas Core Web Vitals como referências:

- LCP: até 2,5 segundos.
- INP: até 200 milissegundos.
- CLS: até 0,1.

Essas metas devem ser avaliadas em condições apropriadas de medição; resultados de laboratório e dados de uso real precisam ser distinguidos.

Como referência complementar, buscar pontuações elevadas nas auditorias Lighthouse, sem confundir pontuação com prova integral de qualidade.

## 47. OTIMIZAÇÕES

Verificar:

- Tamanho do JavaScript.
- CSS desnecessário.
- Fontes e carregamento.
- Recursos bloqueantes.
- Re-renderizações.
- Manipulações repetitivas do DOM.
- Filtros sobre listas extensas.
- Estratégias de cache.
- Uso de dependências externas.
- Tempo de resposta às interações.

Não sacrificar manutenção para otimizações irrelevantes.

## 48. CONFIABILIDADE

A aplicação deve apresentar comportamento previsível diante de:

- Conexão interrompida.
- Armazenamento indisponível.
- Erros de importação.
- Atualização de versão.
- Dados inválidos.
- Ações repetidas.
- Navegação inesperada.
- Carregamentos incompletos.

O erro deve ser tratado e explicado, não ignorado.

---

# PARTE XV — TESTES OBRIGATÓRIOS

## 49. ESTRATÉGIA DE QUALIDADE

Implemente uma estratégia proporcional ao projeto, incluindo:

- Testes unitários.
- Testes de integração.
- Testes end-to-end.
- Testes responsivos.
- Testes de acessibilidade.
- Testes de persistência.
- Testes de regressão.
- Testes de build.
- Verificação da publicação.

Utilize ferramentas apropriadas à arquitetura existente.

Playwright, Vitest e ferramentas de acessibilidade podem ser adotados quando tecnicamente justificáveis.

## 50. CENÁRIOS FUNCIONAIS MÍNIMOS

| ID | Teste obrigatório | Resultado esperado |
|---|---|---|
| T01 | Criar registro | Registro persistido e listado |
| T02 | Editar registro | Alterações refletidas em todos os módulos |
| T03 | Concluir tarefa | Situação e indicadores atualizados |
| T04 | Excluir registro | Confirmação e remoção coerente |
| T05 | Aplicar filtros | Resultado correto |
| T06 | Pesquisar | Correspondências corretas |
| T07 | Limpar filtros | Listagem restaurada |
| T08 | Criar compromisso | Datas e horários corretos |
| T09 | Usar calendário mobile | Seleção por toque funcional |
| T10 | Captura rápida | Prévia, edição e confirmação |
| T11 | Consultar Vânia | Resposta compatível com capacidades reais |
| T12 | Confirmar ação de Vânia | Registro atualizado corretamente |
| T13 | Gerar resumo matinal | Informações do dia correto |
| T14 | Gerar resumo vespertino | Conclusões da data correta |
| T15 | Exportar backup | Arquivo válido e completo |
| T16 | Importar backup | Dados válidos restaurados |
| T17 | Importar dados legados | Migração segura |
| T18 | Atualizar aplicativo | Sem perda de dados |
| T19 | Navegar offline | Recursos locais suportados funcionam |
| T20 | Publicar GitHub Pages | URL e recursos carregam corretamente |
| T21 | Falha de armazenamento | Erro explícito, sem falso sucesso |
| T22 | Envio duplicado | Sem duplicação indevida |
| T23 | Entrada maliciosa | Conteúdo tratado como dado |
| T24 | Histórico de navegação | Retorno coerente |
| T25 | Tela vazia | Orientação útil e funcional |

Cada cenário deve ser implementado como teste automatizado sempre que possível.

Quando não puder ser automatizado, descrever a verificação manual realizada.

## 51. TESTE DE JORNADAS REAIS

Validar no mínimo estas jornadas completas:

**Jornada A — Organização do dia**

Abrir aplicativo → consultar prioridades → abrir tarefa → atualizar tarefa → voltar à tela inicial → verificar atualização.

**Jornada B — Captura rápida**

Escrever informação → revisar interpretação → editar sugestão → confirmar → localizar registro.

**Jornada C — Conversa funcional**

Enviar mensagem a Vânia → receber sugestão estruturada → confirmar → visualizar registro → editar.

**Jornada D — Compromisso**

Criar compromisso → selecionar data e hora → salvar → consultar resumo → reagendar.

**Jornada E — Recuperação**

Pesquisar registro → aplicar filtros → abrir detalhe → editar → retornar à listagem.

**Jornada F — Backup**

Exportar dados → validar arquivo → importar em ambiente de teste → comparar integridade.

**Jornada G — Atualização**

Carregar dados da versão anterior → atualizar aplicação → migrar se necessário → comparar registros e verificar operação.

Essas jornadas são essenciais para identificar falhas que testes isolados não revelam.

## 52. TESTES RESPONSIVOS

Executar verificações em todos os tamanhos especificados.

Registrar, conforme possível:

- Capturas visuais.
- Erros de layout.
- Elementos cortados.
- Sobreposições.
- Problemas de interação.
- Comportamento de modais.
- Comportamento do teclado.
- Uso da navegação inferior.

Dar atenção especial ao Safari do iPhone.

Emulação de navegador não equivale integralmente a teste em aparelho real.

## 53. CRITÉRIOS DE BLOQUEIO

Não considerar a versão aprovada quando ocorrer qualquer falha crítica como:

- Perda ou corrupção de dados.
- Navegação essencial quebrada.
- Botão principal sem funcionamento.
- Persistência inconsistente.
- Contadores incorretos após operação.
- Código contendo credenciais.
- Build quebrado.
- Aplicação publicada retornando erro.
- Incompatibilidade grave com dispositivos-alvo.
- Funcionalidades anunciadas como reais sem implementação.
- Erro de acesso a módulos essenciais.

Falhas menores deverão ser registradas, classificadas e corrigidas conforme prioridade antes do encerramento definitivo do escopo.

---

# PARTE XVI — IMPLEMENTAÇÃO EM FASES

## 54. FASE 1 — AUDITORIA E FUNDAÇÕES

Executar:

- Inventário funcional.
- Diagnóstico do código.
- Avaliação de riscos.
- Linha de base.
- Matriz de requisitos.
- Testes de regressão iniciais.
- Planejamento técnico objetivo.

**Critério de saída:** arquitetura compreendida, riscos principais mapeados e plano de implementação baseado no código real.

## 55. FASE 2 — DESIGN SYSTEM

Implementar:

- Tokens.
- Tipografia.
- Cores.
- Superfícies.
- Botões.
- Campos.
- Cards.
- Estados.
- Feedback.
- Componentes básicos.
- Padrões de acessibilidade.

**Critério de saída:** componentes reutilizáveis implementados e visualmente coerentes.

## 56. FASE 3 — NAVEGAÇÃO E ESTRUTURA

Implementar:

- Sidebar.
- Navegação inferior.
- Organização das telas.
- Estados ativos.
- Histórico.
- Responsividade estrutural.
- Tratamento de rotas.

**Critério de saída:** navegação funcional e consistente em desktop e mobile.

## 57. FASE 4 — DASHBOARD

Implementar:

- Cabeçalho contextual.
- Indicadores reais.
- Foco prioritário.
- Captura rápida.
- Resumo compacto.
- Estados vazios.
- Ações contextuais.

**Critério de saída:** dashboard funcional, integrado à mesma base de registros.

## 58. FASE 5 — REGISTROS

Implementar:

- Busca.
- Filtros.
- Ordenação.
- Listagem.
- Detalhamento.
- Criação.
- Edição.
- Conclusão.
- Reagendamento.
- Arquivamento.
- Exclusão.
- Calendários.
- Validações.

**Critério de saída:** ciclo de vida completo dos registros validado.

## 59. FASE 6 — VÂNIA E ESPECIALISTAS

Implementar:

- Interface conversacional.
- Estados operacionais.
- Sugestões.
- Respostas estruturadas.
- Confirmação de ações.
- Integração com registros.
- Organização da equipe.
- Roteamento local verificável.

**Critério de saída:** conversas e ações funcionais, sem simulação de integrações.

## 60. FASE 7 — RESUMOS E ALERTAS

Implementar:

- Resumo matinal.
- Resumo vespertino.
- Recortes temporais.
- Consulta histórica.
- Política de prioridades.
- Agrupamento de alertas.
- Configurações correspondentes.

**Critério de saída:** dados e períodos corretos, com recursos indisponíveis devidamente identificados.

## 61. FASE 8 — DADOS E CONFIABILIDADE

Implementar:

- Migrações necessárias.
- Backup.
- Importação.
- Tratamento de erros.
- Persistência.
- Histórico apropriado.
- Verificações de consistência.

**Critério de saída:** integridade demonstrada em testes de alteração, atualização e recuperação.

## 62. FASE 9 — PWA, ACESSIBILIDADE E DESEMPENHO

Executar:

- Revisão do manifest.
- Service worker.
- Estratégia offline.
- Atualização de cache.
- Auditoria de acessibilidade.
- Otimizações.
- Testes mobile completos.

**Critério de saída:** aplicação utilizável, acessível e atualizável nos ambientes suportados.

## 63. FASE 10 — PUBLICAÇÃO E HOMOLOGAÇÃO

Executar:

- Testes finais.
- Revisão de dependências.
- Build.
- Verificação de segurança.
- Revisão do diff.
- Commit rastreável.
- Integração controlada à branch principal.
- Workflow de publicação.
- Verificação da URL publicada.
- Smoke tests pós-publicação.
- Relatório final.

**Critério de saída:** versão publicada e verificada, com evidências e limitações documentadas.

---

# PARTE XVII — GITHUB E PUBLICAÇÃO

## 64. PROCEDIMENTO DE VERSIONAMENTO

Utilizar o repositório oficial.

Antes de alterar:

- Identificar branch atual.
- Verificar alterações preexistentes.
- Evitar sobrescrever trabalho não relacionado.
- Registrar a versão inicial.
- Definir estratégia de branch e commits.

Preferir evolução rastreável por commits temáticos.

Para alterações substanciais, utilizar branch de trabalho e integração controlada, preservando a estabilidade da branch principal.

Não criar commits genéricos com dezenas de alterações sem descrição.

## 65. GITHUB PAGES

A aplicação deve permanecer compatível com:

`https://fhenriquefcruz.github.io/orbita/`

Verificar:

- Base path `/orbita/`.
- Referências relativas de arquivos.
- Assets.
- CSS.
- JavaScript.
- Manifest.
- Service worker.
- Roteamento.
- Configuração da publicação.
- Branch ou workflow de origem.
- Status do deploy.

Não considerar a publicação concluída apenas porque o workflow terminou.

Abra a URL efetiva e valide o carregamento.

Erros 404 devem ser investigados conforme configuração, caminho, artefato publicado e roteamento.

## 66. VALIDAÇÃO EM PRODUÇÃO

Após publicar, verificar:

- A página abre.
- Os recursos carregam.
- A navegação funciona.
- O console não apresenta erros críticos.
- A persistência opera.
- O layout corresponde à nova versão.
- O service worker permite atualização.
- As principais jornadas funcionam.
- Não existem recursos externos indisponíveis apresentados como operacionais.

Se o ambiente não oferecer acesso para essa validação, registrar como **não verificado em produção**, nunca como aprovado.

---

# PARTE XVIII — PADRÃO DE QUALIDADE VISUAL

## 67. AVALIAÇÃO VISUAL OBRIGATÓRIA

Não basta aplicar as cores e componentes.

Revise a composição inteira de cada tela.

Avalie:

- Equilíbrio visual.
- Hierarquia.
- Espaçamento.
- Contraste.
- Densidade informacional.
- Alinhamentos.
- Legibilidade.
- Padrões de interação.
- Agrupamento lógico.
- Consistência entre módulos.
- Uso de superfícies.
- Coerência das cores.
- Qualidade de estados vazios.
- Redução de informações repetidas.

### 67.1 Sinais de implementação insatisfatória

Considere insatisfatório qualquer resultado que apresente:

- Muitos cards competindo pelo olhar.
- Textos longos sem necessidade.
- Botões excessivamente grandes.
- Múltiplas ações primárias.
- Cabeçalhos ocupando espaço demais.
- Menus confusos.
- Elementos visualmente desconectados.
- Estilos inconsistentes.
- Gráficos meramente decorativos.
- Cores de situação sem significado uniforme.
- Espaços vazios desproporcionais.
- Componentes desalinhados.
- Cards gigantes para informações simples.
- Desktop bonito e mobile negligenciado.
- Mobile com controles fora da área útil.

### 67.2 Critério de refinamento

Após implementar uma tela, realize uma revisão adicional exclusivamente para detectar imperfeições visuais e problemas de usabilidade.

Não avance considerando que a primeira composição é necessariamente definitiva.

Faça ajustes coerentes com o design system, sem introduzir personalizações isoladas que prejudicarão a manutenção.

---

# PARTE XIX — CONTROLE DE ESCOPO E RASTREABILIDADE

## 68. MATRIZ DE EXECUÇÃO

Mantenha uma matriz que relacione:

**Requisito → Implementação → Arquivo → Teste → Resultado → Evidência**

Exemplo:

| Requisito | Implementação | Teste | Resultado |
|---|---|---|---|
| ORB-UX-001 | Navegação inferior mobile | Navegação por toque | A verificar |
| ORB-FUN-001 | Captura rápida | Criação confirmada | A verificar |
| ORB-DATA-001 | Migração de registros | Compatibilidade legada | A verificar |

Não marcar itens como aprovados sem execução dos testes correspondentes.

## 69. ESTADOS PERMITIDOS DE ENTREGA

Utilizar somente:

- **Não iniciado:** nenhuma implementação.
- **Em andamento:** desenvolvimento iniciado.
- **Implementado, não testado:** código produzido sem validação suficiente.
- **Em validação:** testes em execução.
- **Aprovado:** requisitos e testes atendidos.
- **Reprovado:** falha constatada.
- **Bloqueado:** dependência identificada impede execução.
- **Fora do escopo aprovado:** recurso não previsto e explicitamente separado.

Não utilizar "concluído" como sinônimo de "o código foi escrito".

## 70. TRATAMENTO DE IMPEDIMENTOS

Se houver impedimento:

1. Identifique-o precisamente.
2. Explique o impacto.
3. Determine quais requisitos são afetados.
4. Implemente o que ainda for tecnicamente possível.
5. Não introduza soluções falsas.
6. Registre o teste ou evidência pendente.
7. Indique a dependência necessária.
8. Continue outras etapas independentes.

Não interrompa toda a evolução quando apenas uma integração externa estiver bloqueada.

## 71. CONTINUIDADE ENTRE ETAPAS

Ao concluir uma fase:

- Atualize a matriz.
- Registre os arquivos alterados.
- Execute os testes relevantes.
- Corrija problemas descobertos.
- Registre a decisão técnica.
- Avance para a próxima fase viável.

Não substitua evolução por sucessivas propostas teóricas.

Se a execução for interrompida por limite do ambiente, produza um checkpoint objetivo contendo estado real do código, testes, pendências, alterações não integradas e próximo passo reproduzível.

Esse checkpoint não autoriza afirmar que o trabalho continuará automaticamente fora da sessão.

---

# PARTE XX — DEFINITION OF DONE

## 72. CRITÉRIOS FINAIS DE ACEITAÇÃO

O ORBITA 3.0 somente poderá ser considerado integralmente entregue quando as condições abaixo forem verificadas ou formalmente identificadas como dependências externas fora do escopo funcional local.

### Interface e experiência

- [ ] Identidade visual consistente.
- [ ] Hierarquia clara em todas as telas.
- [ ] Navegação desktop funcional.
- [ ] Navegação mobile funcional.
- [ ] Botões com ações reais.
- [ ] Componentes e estados padronizados.
- [ ] Ausência de poluição visual significativa.
- [ ] Estados vazios úteis.
- [ ] Feedback coerente.
- [ ] Ausência de controles falsamente operacionais.

### Dashboard

- [ ] Indicadores calculados a partir de registros reais.
- [ ] Cards encaminham para filtros corretos.
- [ ] Área de foco utiliza regras consistentes.
- [ ] Captura rápida funciona.
- [ ] Alterações refletem nos indicadores.
- [ ] Ausência de duplicação de informações desnecessárias.

### Vânia

- [ ] Conversa funcional.
- [ ] Modo operacional transparente.
- [ ] Histórico coerente.
- [ ] Sugestões contextuais.
- [ ] Respostas estruturadas quando aplicáveis.
- [ ] Confirmações executam ações reais.
- [ ] Especialistas preservados.
- [ ] Ausência de capacidades fictícias.

### Registros

- [ ] Criação.
- [ ] Consulta.
- [ ] Edição.
- [ ] Conclusão.
- [ ] Reagendamento.
- [ ] Arquivamento.
- [ ] Exclusão confirmada.
- [ ] Busca.
- [ ] Filtros.
- [ ] Ordenação.
- [ ] Calendários.
- [ ] Validações.
- [ ] Integridade entre módulos.

### Resumos e alertas

- [ ] Resumo matinal correto.
- [ ] Resumo vespertino correto.
- [ ] Datas corretas.
- [ ] Conclusões históricas diferenciadas.
- [ ] Alertas sem duplicação indevida.
- [ ] Prioridades coerentes.
- [ ] Integrações não operacionais identificadas.

### Dados e segurança

- [ ] Dados existentes preservados em testes de migração.
- [ ] Exportação funcional.
- [ ] Importação validada.
- [ ] Falhas de persistência tratadas.
- [ ] Nenhuma credencial pública.
- [ ] Entradas não confiáveis tratadas com segurança.
- [ ] Sem falsa sincronização.
- [ ] Limitações de privacidade explicadas.

### Responsividade e acessibilidade

- [ ] Larguras de referência verificadas.
- [ ] Nenhuma rolagem horizontal involuntária.
- [ ] Nenhuma sobreposição relevante.
- [ ] Campos de data utilizáveis por toque.
- [ ] Layout de conversa com teclado aberto.
- [ ] Navegação por teclado.
- [ ] Contraste apropriado.
- [ ] Foco visível.
- [ ] Semântica acessível.
- [ ] Preferência por movimento reduzido respeitada.
- [ ] Testes reais ou limitações de dispositivo documentadas.

### Engenharia e publicação

- [ ] Arquitetura documentada.
- [ ] Componentes reutilizáveis.
- [ ] Testes principais automatizados.
- [ ] Testes de regressão aprovados.
- [ ] Build correto.
- [ ] PWA validado.
- [ ] Service worker atualizado corretamente.
- [ ] GitHub Pages configurado.
- [ ] Aplicação publicada verificada.
- [ ] Alterações versionadas.
- [ ] Relatório final produzido.

**Um único requisito crítico reprovado impede classificar a entrega global como aprovada.**

Itens bloqueados por infraestrutura externa não podem ser convertidos artificialmente em requisitos concluídos.

---

# PARTE XXI — FORMATO OBRIGATÓRIO DE PRESTAÇÃO DE CONTAS

## 73. RELATÓRIO POR FASE

Após cada fase relevante, apresentar:

**1. Objetivo da fase**  
O que precisava ser alcançado.

**2. Entregas implementadas**  
O que realmente foi desenvolvido.

**3. Arquivos alterados**  
Relação objetiva dos principais arquivos.

**4. Decisões técnicas**  
Justificativas para alterações relevantes.

**5. Testes executados**  
Comandos, cenários e resultados.

**6. Falhas corrigidas**  
Problemas identificados e resolvidos.

**7. Limitações**  
O que não foi concluído ou verificado.

**8. Evidências**  
Commits, testes, resultados e URLs quando disponíveis.

**9. Situação da fase**  
Aprovada, reprovada, em validação ou bloqueada.

**10. Continuidade**  
Próxima etapa tecnicamente executável.

## 74. RELATÓRIO FINAL

Ao término, produzir um relatório executivo e técnico contendo:

- Resumo da evolução.
- Comparação entre situação inicial e final.
- Matriz de requisitos.
- Módulos entregues.
- Melhorias visuais.
- Melhorias funcionais.
- Modificações arquiteturais.
- Resultado dos testes.
- Verificação de responsividade.
- Resultado de acessibilidade.
- Verificação de segurança.
- Estado do PWA.
- Estado do Telegram.
- Situação das integrações.
- Preservação dos dados.
- Informações de publicação.
- Limitações remanescentes.
- Roadmap de próximas evoluções.

Diferenciar claramente funcionalidades entregues de recomendações futuras.

Não usar expressões genéricas como "tudo funcionando perfeitamente" sem demonstração objetiva.

---

# PARTE XXII — DIRETRIZES DE DECISÃO AUTÔNOMA

## 75. LIBERDADE TÉCNICA E RESPONSABILIDADE

Você está autorizado a realizar as melhorias locais necessárias à evolução do ORBITA, respeitando preservação de dados, segurança e as condições de acesso disponíveis.

Pode:

- Refatorar componentes.
- Reorganizar estilos.
- Melhorar estados.
- Corrigir erros existentes.
- Refinar navegação.
- Melhorar formulários.
- Consolidar lógicas duplicadas.
- Criar testes.
- Atualizar documentação.
- Melhorar processos de build.
- Corrigir a configuração de publicação.
- Introduzir dependências justificadas.

Não deve:

- Excluir funcionalidades úteis sem análise.
- Reescrever toda a aplicação sem necessidade.
- Trocar tecnologias apenas por tendência.
- Expor segredos.
- Destruir dados.
- Simular integrações.
- Inventar testes.
- Ocultar regressões.
- Marcar itens pendentes como concluídos.
- Criar funcionalidades irrelevantes.
- Complexificar a arquitetura sem benefício concreto.

## 76. ORDEM DE PRIORIDADE DAS DECISÕES

Quando houver conflito, priorize:

1. Integridade e segurança.
2. Funcionamento correto.
3. Clareza funcional.
4. Usabilidade.
5. Acessibilidade.
6. Consistência.
7. Responsividade.
8. Desempenho.
9. Qualidade visual.
10. Sofisticação de detalhes.

Uma interface visualmente impressionante, mas funcionalmente inconsistente, é uma entrega reprovada.

Da mesma forma, uma aplicação funcional, mas confusa e visualmente mal resolvida, ainda não atende ao padrão de produto solicitado.

---

# PARTE XXIII — INSTRUÇÃO FINAL DE EXECUÇÃO

## 77. COMANDO DE INÍCIO

**INICIE AGORA A EVOLUÇÃO DO ORBITA 3.0.**

Execute a auditoria do repositório existente, estabeleça a matriz de requisitos e avance imediatamente para a implementação das melhorias.

Não entregue apenas um planejamento.

Não considere mudanças cosméticas como conclusão do redesign.

Não pare após alterar a primeira tela.

Não negligencie a versão mobile.

Não ignore integrações entre registros, indicadores, resumos e Vânia.

Não substitua testes por declarações.

Não afirme ter publicado algo sem verificar a publicação.

Não remova trabalho existente sem justificativa.

Não introduza controles demonstrativos que pareçam funcionais.

Tome decisões técnicas fundamentadas e avance continuamente entre as fases tecnicamente possíveis, corrigindo falhas antes de considerar cada etapa aprovada.

Mantenha rastreabilidade do que foi desenvolvido.

A execução deve buscar integralmente os critérios de aceite estabelecidos neste documento.

Caso determinada capacidade dependa de serviços, credenciais, infraestrutura ou acessos indisponíveis, preserve a integridade do sistema, registre o impedimento e execute os demais requisitos independentes.

## 78. VISÃO FINAL DO PRODUTO

O ORBITA deve deixar de parecer uma coleção de funcionalidades reunidas em uma página e se tornar uma experiência única e coerente de assessoria pessoal.

**Ao abrir o ORBITA:** o usuário deve sentir tranquilidade, clareza e controle.

**Ao conversar com Vânia:** deve perceber assistência útil, transparente e orientada à ação.

**Ao organizar registros:** deve experimentar simplicidade, consistência e rapidez.

**Ao consultar suas prioridades:** deve entender facilmente o que merece atenção.

**Ao utilizar pelo celular:** deve sentir que a experiência foi realmente projetada para aquele dispositivo.

**Ao confiar suas informações ao produto:** deve compreender os mecanismos e limites reais de armazenamento, proteção e recuperação.

O resultado final desejado é um software elegante, inteligente dentro de suas capacidades reais, responsivo, acessível, confiável, organizado e agradável de usar diariamente.

**Não busco apenas uma interface bonita. Busco um produto excepcional na relação entre funcionalidade, simplicidade, qualidade visual e confiabilidade.**

A tecnologia deve permanecer a serviço da experiência humana.

**ORBITA 3.0 — Menos esforço para organizar. Mais clareza para agir.**

---

**FIM DO PROMPT MESTRE — EXECUÇÃO INTEGRAL ORBITA 3.0**