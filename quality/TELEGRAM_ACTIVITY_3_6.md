# ORBITA 3.6 — Central de atividades Telegram no Aurora

## Entrega (homologação)

Interface em `Dados e histórico → Memória central → Atividades do Telegram`, disponível apenas após Supabase Auth. A lista dos **últimos 100 registros acessíveis à conta** com `payload.source = "Telegram ORBITA"` é consultada por HTTPS/PostgREST mediante JWT e chave publicável, com RLS por titular. **Apenas GET, sem sincronização, mutação ou envio automático.**

### Funcionalidades

- Indicadores compactos de **tarefas em aberto** (`a_fazer` e `em_andamento`), **tarefas concluídas** (`concluida`) e **ideias** (tipo `ideia`).
- Filtro por **Todas**, **Tarefas em aberto**, **Tarefas concluídas**, **Ideias** e busca de títulos sem distinção de maiúsculas/minúsculas ou acentos.
- Título, prioridade válida P0–P3, tipo, `telegram_seq` quando presente, data de atualização válida e situação detalhada (`a_fazer`, `em_andamento`, `concluida`, `cancelada`, `arquivada`, fallback neutro).
- **Atualizar** solicita nova leitura manual. Indicadores refletem apenas a **amostra de até 100 itens**, sem afirmar totalização histórica quando o teto é alcançado.
- Os títulos vindos da nuvem são renderizados por `textContent`; campos numéricos, situações e prioridades são validados antes de exibir.
- Troca de conta durante uma consulta invalida a resposta; sem alteração no `localStorage`.
- Layout móvel, tema noturno, rolagem, navegação e PWA com cache `orbita-pages-v3.6.0-telegram-activity.1`.

### Gates automatizados

Browser smoke com duas identidades simuladas verifica: dados da segunda identidade ausentes; painel protegido; GET sem gravações; 4 itens de teste, contagem 2/1/1, filtros, busca `reuniao` → `Reunião`, estado vazio, texto HTML não executado, refresh e nenhum registro importado localmente. Continua rodando testes de memória pura, backend e varredura de segredos.

### Limitações deliberadas

- A lista principal do Aurora continua local, até que o usuário confirme backup e `Conciliar registros agora`. Filtros não mudam tarefas no Telegram e não alteram o banco.
- Conclusão via `/feito` é feita pelo próprio usuário no Telegram; evitar gravar diretamente nesta etapa.
- Homologação com **duas contas Auth reais**, recuperação de senha no Safari e controle de senhas vazadas permanecem pendentes antes da produção do painel. O mock do navegador e o teste SQL de RLS **não substituem sessões HTTP reais**.
- IA conversacional e notificações continuam desativadas na ausência de configuração explícita pelo proprietário.

## Verificação manual sugerida

1. Entrar na prévia consolidada Aurora com a mesma conta Auth do backend Telegram.
2. Abrir Dados e histórico → Atividades do Telegram e confirmar que a tarefa de teste aparece P1 / A fazer (se não foi concluída).
3. Pesquisar "testar", selecionar "Tarefas em aberto" e clicar Atualizar. Nenhum dado local deve ser criado sem conciliação.
4. Em outro navegador/dispositivo, testar a prévia com uma conta secundária criada de forma autorizada e conferir a ausência de dados do titular, sem compartilhar senhas ou JWTs.
