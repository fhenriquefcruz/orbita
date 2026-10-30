# ORBITA — Homologação real: instruções para o operador

**Status:** roteiro de homologação (não é autorização de produção).
**Projeto exclusivo:** ORBITA / `orbita` / `tbqfymedgdsdrgkqmuni`.
**Branch de teste:** `feat/supabase-auth-protected-panel` (PR #7).
**Não compartilhar:** e-mails pessoais, senhas, JWTs, `sb_secret_`, service_role, códigos de recuperação e backups.

## A. Duas contas autorizadas

1. Abra https://supabase.com/dashboard/project/tbqfymedgdsdrgkqmuni/auth/users
2. Confirme a conta titular existente. Crie ou convide uma segunda conta que **você controle**. Ela deve ser **distinta**, com e-mail confirmado e senha própria.
3. Desabilite inscrição pública quando seu modelo de acesso for convite/administrador, em Authentication > Providers > Email (o nome do controle pode variar).
4. Nunca usar o mesmo navegador/perfil para testar duas contas locais: ORBITA vincula dados locais à identidade. Use dois perfis separados de navegador.

**Critério:** duas contas Auth separadas e confirmadas, sem alterar a identidade já usada pelo Telegram.

## B. Endereços permitidos para recuperação

1. Abra https://supabase.com/dashboard/project/tbqfymedgdsdrgkqmuni/auth/url-configuration
2. Confirme Site URL `https://fhenriquefcruz.github.io/orbita/`.
3. Em Redirect URLs, confira a mesma URL e **adicione apenas para teste local** `http://localhost:8080/`.
4. Se for homologar no iPhone por um preview HTTPS, adicione o **endereço exato** desse preview antes de testar reset. Não inclua `*` para liberar domínios arbitrários.
5. Para e-mails de convite e recuperação em produção, configure e teste SMTP se o serviço padrão tiver limites/restrições.

**Atenção:** o GitHub Pages em `main` **ainda não** publica o PR #7. Não testar o novo login ali até o merge aprovado.

## C. Rodar a versão de teste no computador (sem publicar)

Mac/Linux com Git e Python 3:

```bash
git clone --branch feat/supabase-auth-protected-panel --single-branch https://github.com/fhenriquefcruz/orbita.git
cd orbita
python3 -m http.server 8080 --directory docs
```

Abra `http://localhost:8080/` no computador. Deixe o servidor ligado enquanto testa.

1. Antes de entrar, confirme que **o painel está oculto** e só a tela de login aparece. Teste também `http://localhost:8080/#/records`: registros não devem surgir sem sessão.
2. Entre com a conta titular. Confira `#/home`, `#/records`, `#/chat`, `#/data` e logout.
3. Recarregue a aba autenticada: a sessão deve ser revalidada no servidor e o painel restaurado. Feche a aba e abra outra: pode exigir login novamente.
4. Abra um **perfil de navegador distinto** para a segunda conta. Ela não pode enxergar os dados locais do titular nem registros dele vindos da nuvem. Não tente alternar a identidade do mesmo perfil com dados locais já vinculados.
5. Crie apenas registros fictícios, faça backup local com **Exportar dados**, e só clique em conciliação se tiver autorização para sincronizar fixtures. A conta titular já tem um registro real no PostgreSQL, então não é necessário criar outro para o teste de **leitura**.

## D. Teste real HTTP de RLS sem copiar JWTs

Com as **duas contas confirmadas** e o repositório aberto no computador privado, abra outro Terminal na pasta `orbita`:

```bash
python3 quality/run_auth_homologation.py
```

Digite `HOMOLOGAR` quando solicitado e, em seguida, informe os dois e-mails e senhas **somente no Terminal confiável**. O script faz login por POST em Supabase Auth para abrir sessões e só executa GET na Data API. **Ele não cria, atualiza ou apaga registros**, nem imprime tokens ou dados de usuários. A senha não é exibida. Feche o terminal ao terminar para limitar a permanência de tokens na memória do processo.

- `PASSOU`: duas identidades reais confirmadas pelo Auth, registros isolados por RLS, tabela privada do Telegram e acesso anônimo negados, token inválido recusado.
- `PENDENTE`: o isolamento do chat não pode ser plenamente provado se não houver mensagem do titular. Não fabricar chat em produção somente para marcar sucesso.
- `BLOQUEADO`: confira credenciais, confirmação por e-mail, conexão, chave publicável e concessões, sem enfraquecer o RLS.
- **Mesmo aprovado**, este teste não verifica operações de escrita, sessão expirada, recuperação, Safari ou Telegram em produção.

## E. Recuperação de senha e testes reais

1. Em ambiente de teste, escolha `Esqueci minha senha`. Confirme que a mensagem é enviada ao endereço autorizado.
2. Abra o e-mail no mesmo dispositivo/navegador de homologação, entre pelo link permitido e defina nova senha (mínimo 12 caracteres).
3. Confirme que o link expirado/inválido é recusado e que a aplicação exige novo login após troca.
4. Entre com a nova senha. Faça logout e confira que `#/records` continua bloqueado.
5. A integração GitHub/Vercel registrou o status **Deployment has completed** para o projeto `orbita-web-preview` no commit mais recente. Abra o [deployment do preview](https://vercel.com/rtm11/orbita-web-preview/AccrR4KFTsSKM1KAbUtA51WuJPbn) com sua conta Vercel e use **Visit** para obter a URL HTTPS real. Confirme no painel que está testando a branch do PR, não `main`. A conexão Vercel desta conversa não autorizou consultar diretamente a URL final (recurso não encontrado), portanto a acessibilidade do preview ainda precisa de validação manual.
6. Adicione essa URL exata na allowlist de Redirect URLs do Supabase antes de testar a recuperação de senha no preview. Acesse a mesma URL HTTPS pelo Safari/iPhone, confirme login, logout, recarga, teclado, toque, tela pequena e link de recuperação. Não abrir `localhost` do Mac no iPhone: o iPhone tem seu próprio localhost.

## F. Backup e autorização de gravação

- Abra https://supabase.com/dashboard/project/tbqfymedgdsdrgkqmuni/database/backups
- Como a organização está no **Free**, não presumir backup diário gerenciado: siga a orientação oficial https://supabase.com/docs/guides/platform/backups para um **dump lógico privado** (`supabase db dump`) e um teste de restauração num ambiente descartável.
- Não fazer commit do dump nem de credenciais; não compartilhar pelo chat.
- Com backup validado, preparar **fixtures sem dados reais** para testar SELECT/INSERT/UPDATE/DELETE com dois usuários. Confirmar negação cruzada de edição e exclusão e limpeza controlada.
- Só então revisar migrações opcionais `infra/supabase/002_action_proposals.sql` e `003_telegram_delivery.sql`, uma por vez, com aprovação explícita, nova auditoria e novos testes.
- Testar webhook de Telegram com conta privada/ambiente seguro e deduplicação; não ligar notificações automáticas.

## G. Critérios finais

| Gate | Evidência esperada |
|---|---|
| Identidade | 2 usuários reais com e-mails confirmados |
| Segurança REST | GET isolado, depois INSERT/UPDATE/DELETE isolados |
| UI protegida | Login exigido, sessão restaurada, logout efetivo |
| Recuperação | E-mail real e redefinição concluída |
| Dispositivos | Safari/iPhone, Chrome/Android e desktop |
| Banco | Backup restaurável e advisors revisados |
| Integração Telegram | Testes de permissões, entrega, repetição e falhas |
| Deploy | CI verde e preview HTTPS aprovado antes do merge |

**Somente marcar produção como homologada após evidências reais**, não apenas os testes simulados do GitHub Actions.
