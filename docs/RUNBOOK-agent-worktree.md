# RUNBOOK: Tarefas de agente em Git worktree

## Objetivo

Executar uma tarefa de agente em uma branch e um Git worktree separados,
preservando os arquivos, o staging e a branch `main` do worktree principal
até a integração deliberada. Worktrees compartilham objetos e referências
Git: essa separação não constitui um repositório independente nem uma
fronteira de segurança para o host.

O operador humano executa criação, staging, commit, integração, push e
cleanup. O agente inspeciona, propõe mudanças, edita e valida no worktree
dedicado. Execute cada etapa somente após verificar a anterior; os blocos
abaixo não constituem um script para execução integral sem revisão.

## Pré-condições

Comece no repositório principal, em `main`, com working tree e staging
limpos. Inspecione:

```bash
cd /home/kev-dev/infra
pwd
git rev-parse --show-toplevel
git branch --show-current
git status --short
git diff
git diff --cached
git worktree list
git branch -vv
command -v codex
codex --help
```

O diretório deve ser `/home/kev-dev/infra`, a branch deve ser `main` e
`git status --short` não deve produzir saída. Se houver mudanças, pare e
preserve-as antes de iniciar outra tarefa. Codex deve estar instalado e
configurado; este procedimento não instala ferramentas nem altera sua
configuração ou credenciais.

Confirme que `main` está sincronizada com `origin/main`. Com acesso à rede
autorizado, atualize a referência remota antes de comparar:

```bash
git fetch origin
git rev-list --left-right --count main...origin/main
git rev-parse main origin/main
```

Exija `0 0` e hashes iguais. Sem fetch bem-sucedido, a comparação só
confirma igualdade com a referência remota local, possivelmente antiga;
pare se não puder confirmar a sincronização. Se houver diferença, resolva
a situação da `main` conscientemente antes de criar o worktree.

Defina o escopo, os testes e um nome curto e identificável para a tarefa.
Docker rootless e outras dependências não devem ser modificados
implicitamente. Se a tarefa usar Docker, inspecione `docker context show`
e exija `rootless`; não use o daemon rootful nem `/var/run/docker.sock`.
Se faltarem dependências, pare e combine a solução antes de instalar ou
reconfigurar qualquer coisa.

## Convenção de nomes

Use um slug em minúsculas, com palavras separadas por hífen:

- branch: `agent/<task-slug>`;
- diretório: `/home/kev-dev/worktrees/kev-infra/codex-<task-slug>`.

Nos comandos seguintes, defina as variáveis no terminal do operador.
Substitua `ajustar-documentacao` pelo slug da tarefa. Ao abrir outro
terminal, redefina as mesmas variáveis antes de usá-las.

```bash
TASK_SLUG=ajustar-documentacao
AGENT_BRANCH="agent/$TASK_SLUG"
AGENT_WORKTREE="/home/kev-dev/worktrees/kev-infra/codex-$TASK_SLUG"
MAIN_WORKTREE=/home/kev-dev/infra
git check-ref-format --branch "$AGENT_BRANCH"
git branch --list "$AGENT_BRANCH"
test ! -e "$AGENT_WORKTREE"
```

A validação do nome deve passar, a listagem da branch deve estar vazia e
o teste do caminho deve retornar sucesso. Se o nome ou caminho já existir,
inspecione-o e escolha outro slug; não remova trabalho para reutilizá-lo.
Nomes usados em laboratórios anteriores não são padrões obrigatórios.

## Criação

No worktree principal, após satisfazer as pré-condições:

```bash
git worktree add -b "$AGENT_BRANCH" "$AGENT_WORKTREE" main
git worktree list
git branch -vv
git -C "$AGENT_WORKTREE" status --short
git -C "$AGENT_WORKTREE" branch --show-current
git rev-parse main "$AGENT_BRANCH"
```

`-b` cria a branch indicada; o comando cria o diretório físico e faz seu
checkout a partir do commit atual de `main`, explicitamente indicado como
ponto inicial. Confirme o caminho, a branch correta, o estado limpo e os
hashes iniciais iguais. A `main` continua no worktree principal.

## Execução do agente

Inicie Codex de dentro do worktree dedicado:

```bash
cd "$AGENT_WORKTREE"
pwd
git status
git branch --show-current
codex --sandbox workspace-write --ask-for-approval on-request
```

Antes de executar a última linha, confirme o caminho esperado, a branch
`agent/<task-slug>` e o estado limpo. Entregue ao agente o escopo, os
critérios de aceitação e as restrições da tarefa.

- `AGENTS.md` continua aplicável e deve ser lido antes de alterações.
- O sandbox é a fronteira técnica; `workspace-write` não concede permissão
  irrestrita no host. Worktree é uma separação de trabalho, não um sandbox.
- Ações fora do sandbox devem exigir aprovação explícita. `on-request`
  permite ao agente solicitar aprovação; não significa que todo comando
  será confirmado individualmente. Não desabilite o sandbox para contornar
  uma recusa nem amplie os diretórios graváveis implicitamente.
- Não conceda `sudo` automaticamente; privilégio adicional exige explicar
  necessidade, recurso, menor privilégio e alternativas, conforme `AGENTS.md`.
- Não faça push automaticamente, não acesse secrets ou chaves privadas e
  não altere infraestrutura fora do escopo da tarefa.

## Trabalho do agente

Siga o ciclo:

    inspecionar → planejar → alterar → testar
        → revisar documentação → mostrar git status/diff

Faça a menor alteração necessária e execute os testes pertinentes.
Revise `ARCHITECTURE.md` e os mapas locais quando a estrutura mudar;
preserve a natureza histórica de ADRs, LABs e baselines.

O agente não deve executar `git add`, `git commit` ou `git push`, salvo
quando uma tarefa futura definir explicitamente outro fluxo. Ao entregar,
mostre `git status`, `git diff`, os arquivos novos e os resultados reais
de validação. Não declare testes não executados como aprovados.

## Revisão humana

Encerre ou pause a edição pelo agente durante a revisão. A partir do
worktree principal, use `git -C` para inspecionar o worktree dedicado:

```bash
cd "$MAIN_WORKTREE"
git -C "$AGENT_WORKTREE" status
git -C "$AGENT_WORKTREE" diff
git -C "$AGENT_WORKTREE" diff --check
git -C "$AGENT_WORKTREE" diff --cached
git -C "$AGENT_WORKTREE" ls-files --others --exclude-standard
git -C "$AGENT_WORKTREE" diff --summary
```

Arquivos não rastreados não aparecem no `git diff` normal, inclusive em
`--check`. Leia integralmente cada arquivo novo da listagem, usando, por
exemplo, `less "$AGENT_WORKTREE/caminho/do/arquivo"`, com o caminho real.
Confira também whitespace e conteúdo indevido nesses arquivos. Não abra
secrets: se identificar um arquivo sensível, interrompa a revisão desse
arquivo e trate a situação com o responsável sem expor seu conteúdo.

Execute os testes apropriados dentro do worktree do agente e confira os
resultados. Para scripts/executáveis, inspecione também as permissões com
`stat -c '%A %a %n' "$AGENT_WORKTREE/caminho/do/script"` e revise mudanças
de modo exibidas por `git diff --summary`. Investigue staging inesperado.
Se houver ajustes, retorne ao ciclo do agente e revise novamente.

## Staging e commit

Somente após aprovação humana, o operador prepara os arquivos pretendidos.
Substitua os caminhos de exemplo pelos arquivos efetivamente aprovados;
evite adicionar indiscriminadamente todo o diretório.

```bash
git -C "$AGENT_WORKTREE" add -- caminho/aprovado-1 caminho/aprovado-2
git -C "$AGENT_WORKTREE" diff --cached --check
git -C "$AGENT_WORKTREE" diff --cached --stat
git -C "$AGENT_WORKTREE" diff --cached --name-status
git -C "$AGENT_WORKTREE" diff --cached
git -C "$AGENT_WORKTREE" status
git -C "$AGENT_WORKTREE" diff
```

Confira que o staging corresponde exatamente à aprovação, incluindo os
arquivos novos. Corrija qualquer falha antes de continuar. Crie um commit
assinado, com mensagem adequada às convenções:

```bash
git -C "$AGENT_WORKTREE" commit -S -m "docs(runbook): document agent workflow"
git -C "$AGENT_WORKTREE" verify-commit HEAD
git -C "$AGENT_WORKTREE" status --short
```

Adapte a mensagem à tarefa. Exija verificação bem-sucedida da assinatura
e working tree limpo. Se a assinatura falhar, pare; não contorne com commit
sem assinatura nem acesse chaves privadas para diagnosticar.

## Revisão entre branches

No principal, confira tudo que a branch do agente adiciona à `main`:

```bash
cd "$MAIN_WORKTREE"
git log --oneline --decorate "main..$AGENT_BRANCH"
git diff --stat "main..$AGENT_BRANCH"
git diff "main..$AGENT_BRANCH"
git diff --check "main..$AGENT_BRANCH"
git log --show-signature "main..$AGENT_BRANCH"
```

Esses comandos correspondem a `git log main..agent/<task-slug>` e
`git diff main..agent/<task-slug>`, com o slug escolhido. O log lista
commits exclusivos da branch; o diff compara as árvores nas duas pontas.
Revise todos os commits, arquivos e assinaturas, não apenas o último commit.
Se houver vários commits, execute `git verify-commit <hash>` para cada um
dos hashes listados antes de integrar.

## Integração

Confirme novamente `main` no principal, limpa, e o worktree do agente
limpo. Atualize `origin/main` com rede autorizada e exija igualdade com
`main`; se houver diferença, pare para reconciliar antes de integrar.

```bash
cd "$MAIN_WORKTREE"
git branch --show-current
git status --short
git -C "$AGENT_WORKTREE" status --short
git fetch origin
git rev-list --left-right --count main...origin/main
git merge --ff-only "$AGENT_BRANCH"
```

Execute o merge somente se as verificações anteriores passarem. O fluxo
normal usa `--ff-only` para avançar `main` sem criar um commit de merge,
preservando a sequência revisada e recusando uma integração divergente.
Após sucesso, revise `git status`, `git log --oneline --decorate -4` e
execute a validação apropriada na `main` integrada.

## Caso main tenha avançado

Se `git merge --ff-only` recusar porque as branches divergiram, pare.
Não force o merge, não use `reset --hard` e não descarte commits para
fazer a integração funcionar. Diagnostique somente por inspeção:

```bash
git status
git branch -vv
git log --graph --oneline --decorate main "$AGENT_BRANCH" origin/main
git merge-base main "$AGENT_BRANCH"
git log --left-right --oneline "main...$AGENT_BRANCH"
git diff --stat "main..$AGENT_BRANCH"
git diff "main..$AGENT_BRANCH"
```

Decida conscientemente com o responsável como atualizar ou reconciliar a
branch, considerando o trabalho e se os commits já foram compartilhados.
Rebase ou merge não são soluções automáticas universais. Qualquer solução
deve preservar o trabalho, respeitar as autorizações e ser seguida de nova
revisão, testes e verificação das assinaturas antes de tentar integrar.

## Push

Somente depois da integração, dos testes e da revisão final da `main`,
o operador pode publicar a `main`, com autorização explícita para push e
acesso à rede. Inspecione primeiro:

```bash
cd "$MAIN_WORKTREE"
git branch --show-current
git status --short
git fetch origin
git log --oneline --decorate origin/main..main
git diff --stat origin/main..main
git diff origin/main..main
git diff --check origin/main..main
git log --oneline main..origin/main
git log --show-signature origin/main..main
git verify-commit HEAD
```

Exija `main` limpa, nenhuma entrada em `main..origin/main` e aprovação de
toda a diferença a enviar. Verifique com `git verify-commit <hash>` cada
commit a enviar, caso haja mais de um. Se o remoto tiver avançado, pare
para diagnosticar e reconciliar; não use force push.

```bash
git push origin main
git fetch origin
git rev-parse main origin/main
git rev-list --left-right --count main...origin/main
git status --short
```

Confirme fetch bem-sucedido, hashes iguais, contagem `0 0` e estado limpo.
Se push ou confirmação falharem, preserve a branch e o worktree e siga a
seção de falhas. Não declare sincronização apenas pela referência antiga.

## Cleanup

Encerre a sessão do agente e saia do diretório que será removido. Após
confirmar integração e push, inspecione antes de remover:

```bash
cd "$MAIN_WORKTREE"
git -C "$AGENT_WORKTREE" status --short
git -C "$AGENT_WORKTREE" status --short --ignored
git log --oneline "main..$AGENT_BRANCH"
git merge-base --is-ancestor "$AGENT_BRANCH" main
git worktree list
```

Exija worktree limpo, nenhum commit exclusivo da branch e sucesso no
teste de ancestralidade. Arquivos ignorados também podem conter trabalho
útil e ser apagados junto com o diretório: preserve os necessários antes
de continuar, sem expor ou versionar secrets.

```bash
git worktree remove "$AGENT_WORKTREE"
git worktree list
git branch -d "$AGENT_BRANCH"
git branch --list "$AGENT_BRANCH"
git status --short
```

Remover o worktree remove seu diretório e registro, mas não remove
automaticamente a branch. `-d` é a remoção segura para a branch já
integrada; se recusar, pare e inspecione. `-D` não faz parte do fluxo
normal: é reservado para descarte consciente e explicitamente autorizado
de trabalho não integrado. Não use remoção forçada do worktree.

Ao final deste fluxo, `git worktree list` deve mostrar somente o principal
em `main`, e a listagem da branch temporária deve estar vazia. Se houver
outros worktrees de tarefas independentes, preserve-os e registre essa
exceção; não os remova para satisfazer o checklist.

## Falhas e abortos

Interrompa etapas dependentes sempre que uma verificação falhar.

| Situação | Procedimento seguro |
| --- | --- |
| Agente deixou mudanças não commitadas ou worktree sujo | Pare o agente, inspecione status, diff, staging e arquivos novos. Mantenha o worktree; retome revisão e testes ou combine como preservar o trabalho. Não remova nem limpe automaticamente. |
| Branch não integrada | Inspecione `main..<branch>` e o grafo. Preserve branch e worktree até decidir entre concluir a integração ou abandonar conscientemente. |
| `git branch -d` recusa | Não troque por `-D`. Inspecione ancestralidade e commits restantes; se o worktree já foi removido, a branch ainda preserva os commits. |
| `merge --ff-only` recusa | Pare e use apenas os comandos de diagnóstico da seção sobre avanço de `main`; decida a reconciliação antes de alterar o histórico. |
| Push falha ou confirmação remota falha | Preserve commits locais e worktree. Inspecione status e grafo; com rede autorizada, faça fetch e compare as referências. Resolva a causa antes de tentar novamente; não force push nem exponha credenciais. |
| Usuário abandona a tarefa | Pare o agente, inventarie commits, mudanças rastreadas, arquivos novos e ignorados. Mantenha o worktree até o usuário decidir o que preservar e autorizar explicitamente qualquer descarte. Não suponha que abandonar autoriza excluir trabalho. |

Um diff isolado não preserva arquivos não rastreados ou ignorados. Não
apague diretórios, branches ou mudanças antes de verificar que o trabalho
necessário foi preservado. Não há cleanup destrutivo automático neste
procedimento.

## Checklist final

- [ ] Pré-condições confirmadas: `main` limpa e sincronizada antes da criação.
- [ ] Worktree criado no caminho e na branch corretos.
- [ ] Agente trabalhou apenas no worktree dedicado e dentro do escopo.
- [ ] Mudanças, arquivos novos, permissões e documentação revisados; testes passaram.
- [ ] Commit assinado e assinatura verificada; branch do agente limpa.
- [ ] Diferenças entre branches e integração fast-forward revisadas.
- [ ] Push concluído; `main` limpa e confirmada igual a `origin/main`.
- [ ] Worktree da tarefa removido.
- [ ] Branch temporária removida com `-d`.
- [ ] Apenas o worktree principal em `main` permanece, salvo tarefas independentes registradas.

## Relação com LAB-0003

O [LAB-0003](LAB-0003-git-worktree-agent-workflow.md) é a evidência
histórica que validou o isolamento de arquivos, `HEAD` e index, o
compartilhamento de objetos e referências e o comportamento da limpeza.
Este runbook transforma essas observações em um procedimento operacional;
nomes, commits e descarte experimental do laboratório não são requisitos
para tarefas futuras.
