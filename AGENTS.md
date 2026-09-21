# AGENTS.md

Este repositório gerencia a infraestrutura do ambiente `kev-dev`.

## Objetivo

Manter o host Ubuntu mínimo, seguro, reproduzível e documentado.

O host funciona como control plane.

Toolchains, bancos de dados, runtimes e serviços específicos de
projetos devem preferencialmente executar em containers.

## Workflow

Antes de alterar qualquer coisa:

1. inspecione o estado atual;
2. entenda a mudança;
3. faça a menor alteração necessária;
4. valide o resultado;
5. revise se documentação precisa ser atualizada.

Não declare uma tarefa concluída sem verificar o resultado.

## Segurança do host

- Não usar `sudo` sem aprovação explícita do usuário.
- Não alterar `/etc`, bootloader, partições, LVM, firewall ou serviços
  do sistema sem aprovação explícita.
- Não instalar pacotes no host sem aprovação explícita.
- Não utilizar `curl | sh` ou equivalente.
- Downloads executáveis devem ser inspecionados e verificados antes da
  execução quando possível.
- Não acessar, imprimir ou modificar chaves SSH privadas, tokens,
  códigos de recuperação ou outros secrets.
- Não copiar secrets para containers ou para o Git.

## Docker

Docker deve permanecer rootless.

Não utilizar o daemon Docker rootful.

Não utilizar:

    /var/run/docker.sock

O contexto esperado é:

    rootless

Containers são descartáveis.

Estado persistente deve utilizar volumes ou bind mounts definidos
explicitamente.

Projetos são isolados por padrão.

Conectividade entre redes deve ser explícita.

Não criar uma rede global para todos os containers.

Portas que precisam ser acessadas somente pelo host devem preferir
bind em:

    127.0.0.1

## Git

Não executar automaticamente:

- `git push`;
- force push;
- `git reset --hard`;
- rebase destrutivo;
- remoção de branches;
- alterações de configuração Git ou SSH.

Commits e pushes devem ocorrer somente quando solicitados pelo usuário.

Antes de propor um commit, revisar:

    git status
    git diff
    git diff --cached

## Documentação

`docs/ARCHITECTURE.md`
    mapa vivo da arquitetura atual.

`docs/CONVENTIONS.md`
    convenções utilizadas no repositório.

`ADR`
    decisão arquitetural histórica.

`LAB`
    experimento técnico e seu resultado.

`BASELINE`
    fotografia histórica de um estado do sistema.

ADRs, LABs e baselines não devem ser reescritos apenas para representar
o estado atual.

Uma mudança estrutural deve verificar se exige atualização de:

- `docs/ARCHITECTURE.md`;
- `docker/README.md`;
- ADR correspondente;
- LAB correspondente;
- README local.

## Laboratórios

Não registrar um experimento como PASS sem que os comandos tenham sido
realmente executados e seus resultados observados.

Arquivos de laboratório devem permanecer reproduzíveis.

## Secrets

Secrets não entram no Git.

Arquivos `.env` reais não devem ser versionados.

Arquivos de exemplo podem conter somente nomes de variáveis,
placeholders ou valores não sensíveis.

## Princípio de privilégio

Privilégio é exceção, não padrão.

Quando uma solução exigir privilégio adicional, explicar primeiro:

- por que é necessário;
- qual recurso precisa dele;
- qual o menor privilégio possível;
- quais alternativas existem.
