# ORBITA 3.2 — Identidade visual Aurora

## Direção
A interface foi redesenhada para ser mais legível, espacial e acolhedora:
- Canvas porcelana com navegação azul-noite, violeta de ação, azul para agenda, âmbar para alta atenção e jade para ideias.
- Tipografia de interface DM Sans com títulos Manrope, ambas opcionais via Google Fonts; fontes de sistema dão suporte à instalação offline.
- Cards de indicadores com distinção por cor **e** rótulo; não se depende apenas de cor para transmitir significado.
- Bordas sutis, hierarquia editorial, botões de pelo menos 42px, foco visível e espaçamento consistente.
- Tema claro padrão e noturno opcional, com escolha local por navegador. Tema não é dado pessoal de negócio.
- Telas menores de 375px, 700px e 1180px recebem ajustes para menu, cartões, filtros e chat.
- Nenhum fluxo de banco, sessão, exportação, memória, respostas do Telegram ou agendamento foi alterado.

## Arquivos
- \`docs/design-aurora.css\`: tokens, layout, componentes, cards, temas, responsividade e visual do login.
- \`docs/theme.js\`: alternância com botão acessível e persistência de preferência visual (somente armazenamento local).
- \`docs/index.html\`: import do design e do tema; atualização da cor de barra do navegador.
- \`docs/manifest.webmanifest\`: atualização de cores e descrição da PWA.
- \`docs/sw.js\`: nova versão do cache e assets da identidade; sem cache de API privada.

## Verificação antes de integrar
- CI Python e JavaScript e smoke Playwright em 8 resoluções.
- Alternar tema e confirmar que o modo é restaurado ao recarregar.
- Validar contrastes de texto das duas paletas, foco visível e ausência de overflow em 320px.
- Comparar página de login, dashboard, cartões, chat, registros, formulário modal, equipe e histórico em desktop e celular.
- Proteger a versão pública: este design se apoia na branch de Auth ainda em homologação.

## Limites e segurança
- A prévia do Vercel pode ser visualizada sem login da Vercel; **o conteúdo pessoal não deve ficar visível sem Supabase Auth**.
- O login real e as políticas RLS com duas contas permanecem pendentes de homologação.
- O painel pode guardar dados locais não criptografados; não colocar dados sensíveis até concluir a migração segura.
