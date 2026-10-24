# Segurança e privacidade

1. Token Telegram: use `/revoke` no BotFather se foi exposto; salve somente em `telegram/.env` ou gerenciador de segredos.
2. API OpenAI: chave no ambiente do bot/servidor, **nunca** no JavaScript do GitHub Pages.
3. Banco SQLite: não versionar, não enviar em issues, não anexar screenshots com dados.
4. Controle de acesso: iniciar com `ORBITA_OWNER_ID=0`, descobrir ID por `/id`, configurar ID correto e reiniciar.
5. O site público não tem autenticação; armazene apenas dados de teste e informações não sensíveis.
6. A futura sincronização exige backend com TLS, autenticação, autorização por usuário, backup e logs sem segredos.
7. Nenhum sistema de notificação foi ativado. Não confundir protótipo visual com agendamento real.

Para reportar problemas de segurança, não publique tokens nem dados pessoais em issues abertas.