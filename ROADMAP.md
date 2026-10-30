# Roadmap ORBITA — estado em 30/10/2026

Referências: [handoff](product/ORBITA_CODEX_HANDOFF.md), [Prompt Mestre 3.0](product/PROMPT_MESTRE_ORBITA_3_0.md) e [evidência Auth/RLS](quality/AUTH_RELEASE_GATE.md). O estado desta branch não equivale ao estado publicado em `main`.

## Entregue e verificado

- [x] Painel existente com login Supabase, rotas protegidas e sessão restaurável. A sessão real no navegador integrado do VS Code permaneceu autenticada após recarga; o formulário de login deixou de aparecer durante a verificação.
- [x] Projeto Supabase dedicado ativo com núcleo de registros/chat e RLS. Teste HTTP de duas contas reais e isolamento de registros/chat registrado em 26/10; fixtures removidas.
- [x] Consulta e simulação de conciliação implementadas como leitura; a gravação exige ação e confirmação separadas.
- [x] Consulta e simulação pela interface com uma sessão real: 1 registro remoto, 0 locais; prévia de 1 a receber, sem envios, exclusões ou conflitos. Ver [evidência de 30/10](quality/REAL_MEMORY_UI_20261030.md).
- [x] Jornada local de criar, editar, concluir, pesquisar e filtrar registros, atualizar indicadores/resumos e persistir após F5. Teste de navegador com Auth/Data API simulados passou.
- [x] Proteções de integridade local, tombstones e cache offline com 51 testes JS aprovados nesta sessão.

## Próximo incremento executável

- [ ] Ampliar a homologação da memória central para falhas de rede reais e isolamento de duas contas pela interface, sem gravar registros reais. Falhas Auth 503/401 e renovação foram cobertas com respostas simuladas.
- [ ] Executar regressão completa da CI, incluindo a nova jornada de tarefas, e corrigir falhas concretas.
- [ ] Validar teclado, foco, toque e layout em Safari/iPhone, Chrome/Android e desktop; registrar evidência de dispositivo e corrigir problemas encontrados.
- [ ] Homologar recuperação de senha, logout e sessão expirada com links e perfis autorizados.
- [ ] Verificar backup restaurável em ambiente isolado antes de qualquer migração opcional ou conciliação com escrita.

## Dependente de autorização específica

- [ ] Aplicar `002_action_proposals.sql` ou `003_telegram_delivery.sql` após revisão e gates de backup/segurança.
- [ ] Alterar Telegram ativo, webhook, flags de ações naturais ou entrega V2.
- [ ] Publicar a branch em `main` ou produção e verificar o resultado publicado.
- [ ] Recuperar banco privado; o PostgreSQL nativo não reproduz automaticamente Supabase Auth/RLS. Ver [decisão de recuperação](quality/RECOVERY_SCOPE_DECISION_2026_10_29.md).

## Evolução de produto posterior

- [ ] Conversa por IA com permissões, observabilidade e ações confirmadas.
- [ ] Integração com Google Calendar consentida e verificável.
- [ ] Resumos reais às 07h30/18h e política de silêncio até 07h30, com agendamento, deduplicação e opção de desligar.
- [ ] Revisão contínua de custo, privacidade, acessibilidade e desempenho.

**Regra de aceite:** diferenciar código escrito, teste simulado, evidência real e liberação de produção. Não marcar integração ou automação como operacional por existir fonte ou configuração.
