# ORBITA — Aurora 3.34 | Preparação segura do ambiente de recuperação no Windows

## Evidências do operador — 28/10/2026

- \`quality/private_restore_preflight_windows.ps1\` verificou \`APROVADO - integridade, hash SHA256, ACLs e catalogo conferidos\`.
- \`pg_restore\` e \`psql\`: **17+**, disponíveis.
- \`node.exe --version\`: **v24.19.0**, compatível com CLI via npx.
- \`npx.cmd --yes supabase --version\`: **2.122.0** (funcionou).
- \`docker.exe\`: **não encontrado**.
- **Restauração real NÃO executada**. Flags, migrações 002/003, PR de produção permanecem bloqueadas.

A CLI **não precisa** estar instalada globalmente via Scoop/npm. No PowerShell,
\`npx.cmd\` é apropriado quando a política de execução impede \`npx.ps1\`.
O preflight detecta a CLI pelo comando global e, se não existir, tenta a
versão **já em cache**, via \`npx.cmd --offline --yes supabase --version\`.
O \`--offline\` proíbe download; se a cache não conseguir resolver o pacote,
a saída será **não comprovado pelo script**, mesmo que o operador o tenha
validado separadamente com \`npx.cmd --yes supabase --version\`. Isso não
é motivo para instalar o Scoop.

## Próximo bloqueio real: Docker Desktop

1. Somente leitura no PowerShell: \`wsl.exe --version\`, \`wsl.exe --status\`.
2. Se WSL 2/virtualização estiver compatível, instalar **Docker Desktop
   para Windows**, preferindo instalação por usuário e backend de contêineres
   **Linux/WSL 2**. Revisar necessidade de reinício e direitos do PC.
3. Abrir o Docker Desktop e confirmar o Engine saudável com
   \`docker.exe version\` e \`docker.exe info --format '{{.ServerVersion}}'\`.
4. Repetir o preflight a partir da pasta \`$HOME\orbita\` atualizada.

Referências:
- https://docs.docker.com/desktop/setup/install/windows-install/
- https://supabase.com/docs/guides/local-development/cli/getting-started

## Requisitos de isolamento para a recuperação

**NÃO** executar \`supabase init\` nem \`supabase start\` dentro da pasta Git
\`$HOME\orbita\` por acidente. Depois do Docker funcionar, criar uma
**pasta local exclusiva**, por exemplo \`$HOME\orbita-restore-sandbox\`,
com acesso privado. Nunca usar \`supabase link\`, \`db push\` ou \`db reset\`
no projeto remoto.

O dump validado contém Auth/dados de usuários. **Não** adicionar ao Git,
não anexar a chats nem montar toda a pasta de backups em serviços/containers.
A restauração deve ocorrer apenas em instância isolada e protegida,
preferencialmente com portas vinculadas a \`127.0.0.1\`:

\`\`\`powershell
docker.exe network create -o "com.docker.network.bridge.host_binding_ipv4=127.0.0.1" orbita-restore-local
\`\`\`

O comando acima **cria uma rede Docker local** e deve ser executado
**apenas quando Docker estiver instalado e com o Engine pronto**.
O próximo passo será configurar o projeto local nessa rede e determinar
como restaurar um \`pg_dump --format=custom\` convencional com objetos
Supabase Auth, roles e extensões, com uma estratégia verificável.

**Não usar** \`supabase db start --from-backup\` com este dump custom:
esse fluxo foi documentado para backups de cluster baixados do painel,
formato diferente.

A restauração só será marcada APROVADA após validação de saída,
dados, permissões e Auth em ambiente isolado. Não há autorização de
executar migrações 002/003 ou publicar na produção.
