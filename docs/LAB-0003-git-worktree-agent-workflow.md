# LAB-0003: Isolamento de trabalho com Git worktree

## Objetivo

Validar o isolamento de arquivos, index e commits ao trabalhar em um
worktree secundário, e verificar como seus metadados se relacionam com
os do repositório principal. O experimento representa um fluxo de
trabalho possível para agentes como Codex.

## Hipótese

Um worktree secundário permite trabalhar em outra branch sem alterar
os arquivos, o index ou o `HEAD` do worktree principal. Os objetos e
as referências Git permanecem acessíveis pelo repositório comum.

## Procedimento e resultados observados

1. O worktree principal estava em `/home/kev-dev/infra`, na branch
   `main`. Foi criado um segundo worktree em
   `/home/kev-dev/worktrees/kev-infra/codex-lab`, usando a branch
   `lab/codex-worktree`. Inicialmente, ambos apontavam para `39e03cd`.
2. O arquivo `WORKTREE-LAB.txt` foi criado no worktree secundário e não
   apareceu no principal.
3. `git add` no secundário alterou apenas o index desse worktree. O
   index do principal permaneceu vazio.
4. O commit `5c2daa5` foi criado na branch `lab/codex-worktree`. Ele
   apareceu em `git log --all` no repositório principal, enquanto
   `main` permaneceu em `39e03cd`.
5. O arquivo `.git` do worktree secundário apontava para
   `/home/kev-dev/infra/.git/worktrees/codex-lab`. Esse diretório
   possuía `HEAD` e `index` próprios. Seu arquivo `commondir` continha
   `../..`, apontando para os metadados compartilhados em
   `/home/kev-dev/infra/.git`.

## Modelo observado

- **Branch** é uma referência para um commit. Neste laboratório,
  `main` continuou em `39e03cd` e `lab/codex-worktree` avançou para
  `5c2daa5`.
- **Worktree** é uma árvore de arquivos de trabalho associada a um
  checkout. O arquivo criado no secundário não apareceu no principal.
- **HEAD** identifica a referência ou o commit selecionado em cada
  worktree. O secundário possuía um `HEAD` específico em seu diretório
  de metadados.
- **Index** é a área de preparação de mudanças para commit. Cada
  worktree possuía seu próprio index; preparar o arquivo no secundário
  não preparou nada no principal.

Os arquivos de trabalho, `HEAD` e index eram específicos de cada
worktree. Os metadados comuns, incluindo objetos de commit e
referências de branches, eram compartilhados pelo repositório: por
isso `git log --all` no principal encontrou o commit da outra branch
sem mover `main`.

## Implicações para agentes

Um agente como Codex pode receber um worktree e uma branch dedicados
para editar e preparar mudanças sem afetar diretamente os arquivos e
o index do worktree principal. Commits feitos nessa branch passam a
existir no repositório compartilhado e podem ser vistos por outros
worktrees. Portanto, o isolamento do diretório de trabalho não
equivale a um repositório Git independente.

## Limpeza

`git worktree remove` removeu o diretório físico do worktree
secundário e seu registro. `git branch -d` recusou apagar a branch
porque ela não estava merged. `git branch -D` foi usado
conscientemente para descartar o commit de laboratório.

Ao final, `main` e `origin/main` permaneceram em `39e03cd`, e o
working tree principal ficou limpo.

## Conclusão

**PASS.** O experimento validou o isolamento dos arquivos, do `HEAD`
e do index por worktree, bem como o compartilhamento dos objetos e
das referências Git. A limpeza removeu o worktree temporário e a
branch experimental, preservando o estado da branch principal.
