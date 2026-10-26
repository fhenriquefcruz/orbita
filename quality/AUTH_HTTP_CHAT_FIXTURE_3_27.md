# ORBITA Aurora 3.27 — conclusão do gate HTTP do chat

## Motivo do resultado PENDENTE

O usuário executou a Aurora 3.25 em duas sessões **reais** do Supabase,
com resultado: *Auth e isolamento dos registros passaram, mas não existem
mensagens do titular para comprovar isolamento do chat.*

O painel `docs/index.html` usa `localStorage` para guardar o histórico
quando não está conectado ao backend local. Escrever normalmente no chat
da página **não assegura** que surja uma linha na tabela
`public.orbita_chat_messages` do Supabase. Não confundir os dois meios.

A Aurora 3.26 já validou RLS com duas contas cadastradas e linha temporária
revertida pelo banco, mas não houve prova HTTP cruzada do chat. Esta
ferramenta complementa aquele ensaio, por meio do mesmo endpoint real
PostgREST usado pelo sistema.

## O que o teste opcional faz

`quality/auth_chat_fixture_http.py` é acionado **somente** no computador do
titular, com autorização explícita. Ele:

1. Obtém duas sessões legítimas diretamente do Supabase Auth usando
   senhas digitadas sem exibição (`getpass`).
2. Executa **todos os gates HTTP somente leitura da Aurora 3.24** antes de
   qualquer gravação. Se o chat do titular já contém dados, encerra sem
   inserir nada.
3. Com uma tabela de chat vazia para o titular, faz **um único POST**
   autenticado com a conta principal, criando uma mensagem sintética com
   prefixo `ORBITA_RLS_FIXTURE_` e 32 caracteres aleatórios.
   Nunca usa conteúdo de conversa pessoal.
4. Confirma que o titular consegue ler a própria mensagem, mas a segunda
   conta não consegue vê-la nem excluí-la.
5. Repete o verificador completo Auth/RLS agora com uma linha real de chat.
6. Em `finally`, executa um **DELETE específico** da linha sintética,
   usando a conta proprietária, filtrando simultaneamente `user_id`
   e `content` único, e consulta novamente para **provar ausência**.
7. Não imprime e-mails, UUID, senhas, JWTs, mensagem sintética ou corpo de
   erro HTTP. Não muda usuários, registros reais, tarefas, projetos,
   funções nem schema. Flags Telegram continuam desligadas.

**Limitação importante:** transações de duas chamadas HTTP diferentes
não compartilham um mesmo ROLLBACK. Se a conexão cair ou o processo for
interrompido abruptamente, uma linha sintética pode permanecer no banco.
A ferramenta **não afirma sucesso** quando sua remoção não é comprovada.

## Executar no Windows

Recomendado: execução no computador privado Windows, com branch de
homologação atualizada. Use apenas uma chave `sb_publishable_...`, já
publicada em `docs/cloud-config.js`. Não copiar valores de senhas/tokens
para PowerShell nem para ChatGPT.

```powershell
cd "$HOME\orbita"
git pull --ff-only origin feat/supabase-auth-protected-panel
$env:ORBITA_CHAT_FIXTURE_ACK = "I_AUTHORIZE_ONE_TEMPORARY_CHAT_MESSAGE"
$env:ORBITA_E2E_EXPECT_PROJECT = "tbqfymedgdsdrgkqmuni"
$config = Get-Content ".\docs\cloud-config.js" -Raw
$env:ORBITA_E2E_PUBLISHABLE_KEY = [regex]::Match(
  $config, 'sb_publishable_[A-Za-z0-9_-]+'
).Value

try {
    py .\quality\auth_chat_fixture_http.py
} finally {
    Remove-Item Env:\ORBITA_CHAT_FIXTURE_ACK,Env:\ORBITA_E2E_EXPECT_PROJECT,Env:\ORBITA_E2E_PUBLISHABLE_KEY -ErrorAction SilentlyContinue
}
```

O programa pede e-mail e senha das duas identidades existentes, sem
mostrar senhas. A mensagem final **PASSOU** comprova isolamento real do
chat por HTTP e confirmação de exclusão da linha sintética. **BLOQUEADO**
significa que o teste ou a limpeza não foram comprovados. Antes de tentar
novamente, examine o Supabase e verifique se há uma linha temporária
remanescente.

## Tratamento de falha de limpeza

Se a mensagem disser `BLOQUEADO`, não executar em loop. Confira no
**SQL Editor do projeto ORBITA**, com acesso administrativo autorizado,
a existência de mensagens com conteúdo iniciado por
`ORBITA_RLS_FIXTURE_`. Exemplo **somente leitura**, que não devolve os
conteúdos privados:

```sql
select count(*) as leftover_fixture_rows
from public.orbita_chat_messages
where content like 'ORBITA_RLS_FIXTURE_%';
```

Se existir alguma linha remanescente, valide que pertence ao ensaio e
prepare sua exclusão específica depois de conferência. **Não execute**
remoção genérica em tabelas ou usuários; não use `DELETE` por prefixo
sem inspeção dos identificadores e contexto.

## O que esta etapa NÃO libera

- Uma mensagem sintética temporária **não equivale a backup recuperável**.
- Não aplica SQL 002/003, não muda `main` nem liga Telegram.
- Não comprova recuperação de senha, refresh/logout ou Safari real.
- Não resolve `Leaked Password Protection Disabled`.
- Não é implantação de produção. O relatório de backup privado e teste
  de restauração isolada permanecem exigências para migrações permanentes.

Mesmo que a nova ferramenta retorne PASSOU, a ativação final depende das
demais verificações e de aprovação operacional separada.
