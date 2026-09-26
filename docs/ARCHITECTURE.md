# Architecture

Este documento descreve a arquitetura atual do ambiente `kev-dev`.

Diferente de um baseline, este é um documento vivo:
ele deve ser atualizado sempre que a arquitetura mudar.

---

## Visão geral

    Ubuntu Host
    │
    ├── Aplicações nativas
    │   ├── Brave Browser
    │   ├── Git
    │   ├── OpenSSH client
    │   ├── curl
    │   ├── wget
    │   ├── UFW
    │   └── Codex CLI
    │       ├── command: ~/.local/bin/codex
    │       ├── state/config: ~/.codex
    │       └── credentials: keyring configurado e validado
    │
    ├── Identidade Git/GitHub
    │   ├── SSH authentication
    │   │   └── ~/.ssh/github_auth_ed25519
    │   │
    │   └── SSH commit signing
    │       └── ~/.ssh/github_sign_ed25519
    │
    ├── Docker Engine
    │   │
    │   ├── Serviços rootful do sistema
    │   │   ├── docker.service       disabled / inactive
    │   │   ├── docker.socket        disabled / inactive
    │   │   └── containerd.service   disabled / inactive
    │   │
    │   └── Docker rootless
    │       ├── usuário: kev-dev
    │       ├── systemd --user docker.service
    │       ├── context: rootless
    │       ├── socket: /run/user/1000/docker.sock
    │       ├── storage: ~/.local/share/docker
    │       ├── storage driver: overlayfs
    │       └── cgroup: v2
    │
    ├── Armazenamento
    │   ├── NVMe
    │   ├── LVM vg_nvme
    │   │   ├── LV ubuntu
    │   │   ├── LV shared
    │   │   └── espaço livre reservado
    │   └── /shared
    │
    └── ~/infra
        ├── AGENTS.md
        ├── bootstrap/
        ├── docker/
        │   ├── tools/python/
        │   ├── tools/c/
        │   └── labs/
        │       ├── rootless-uid/
        │       ├── dev-python/
        │       ├── dev-c/
        │       ├── network-basic/
        │       ├── volume-basic/
        │       └── shared-network/
        ├── docs/
        │   ├── BASELINE-0.md
        │   ├── ADR-0001-docker-rootless.md
        │   ├── ADR-0002-docker-network-strategy.md
        │   ├── LAB-0001-docker-network-volume.md
        │   ├── LAB-0002-shared-external-network.md
        │   ├── LAB-0003-git-worktree-agent-workflow.md
        │   ├── RUNBOOK-agent-worktree.md
        │   ├── ARCHITECTURE.md
        │   └── CONVENTIONS.md
        ├── scripts/
        │   ├── check-infra
        │   ├── check-dev-python
        │   ├── check-dev-c
        │   └── tests/
        │       └── check-infra-test
        └── system/

---

## Host

O Ubuntu funciona como base mínima de execução.

Ferramentas específicas de projetos devem, sempre que possível,
ficar fora do host e ser executadas em containers.

Exemplos de software que normalmente não deve ser instalado
diretamente no Ubuntu:

- versões específicas de Python;
- Node.js;
- compiladores específicos de projetos;
- PostgreSQL;
- Redis;
- toolchains embarcadas;
- SDKs específicos.

Software nativo deve existir apenas quando fizer sentido como
capacidade do próprio host.

---

## Docker

O Docker Engine principal utiliza modo rootless.

O usuário `kev-dev` não pertence ao grupo `docker` para controlar
um daemon rootful.

Os serviços Docker/containerd rootful do sistema estão desativados.

O daemon utilizado pertence ao ambiente `systemd --user`.

### Socket

    /run/user/1000/docker.sock

### Dados persistentes internos do Docker

    /home/kev-dev/.local/share/docker

### Storage driver

    overlayfs

---

## Modelo de containers

Cada mecanismo deve ser usado para sua finalidade correta:

    imagem/container
        → executáveis, processos e ferramentas

    bind mount / volume
        → arquivos e dados

    rede
        → comunicação entre processos

    secret
        → credenciais e material sensível

Containers devem ser considerados descartáveis.

Dados que precisam sobreviver à destruição de containers
devem ficar em volumes ou em bind mounts deliberadamente definidos.

---

## Redes

O padrão arquitetural é isolamento.

Projetos não devem ser conectados automaticamente a uma única
rede global.

A direção atual da arquitetura é:

    redes internas por projeto
        +
    redes compartilhadas por finalidade
        +
    containers conectados a múltiplas redes somente quando necessário

Exemplo conceitual:

    brsa_internal
    ├── api
    ├── postgres
    └── redis

    metra_internal
    ├── api
    └── simulator

    proxy_net
    ├── reverse-proxy
    ├── brsa-frontend
    └── forgejo

Um container pode pertencer a mais de uma rede quando houver
necessidade explícita.

Bancos de dados e serviços internos não devem ser colocados em
redes compartilhadas sem necessidade.

---

## Containers de ferramentas

Containers de ferramentas não fornecem suas ferramentas pela rede.

Por exemplo, um container Python não fornece o executável `python`
a outro container apenas por estar na mesma rede.

O modelo esperado é:

    código do projeto
          │
          │ bind mount / volume
          ▼
    container dev-python
          │
          └── executa Python localmente

ou:

    código do projeto
       ├── dev-python
       ├── dev-c
       └── dev-embedded

Os containers de ferramentas podem ser conectados à rede de um
projeto quando precisarem acessar seus serviços.

---

## Laboratórios já validados

### LAB-0001

Foram validados:

- comunicação por DNS entre containers da mesma rede;
- isolamento entre redes distintas;
- conexão dinâmica de um container a outra rede;
- restauração do isolamento após desconexão;
- persistência por volume nomeado;
- recriação de container sem perda do volume.

### LAB-0002

Foram validados:

- uso de uma rede externa por projetos Compose independentes;
- comunicação por DNS e HTTP entre projetos distintos;
- independência do ciclo de vida dos projetos;
- preservação da rede após `docker compose down`;
- remoção de serviços do DNS após sua destruição;
- proteção contra remoção da rede enquanto existirem endpoints ativos;
- persistência da rede após a remoção de todos os projetos;
- remoção explícita da rede quando ela deixa de estar em uso.

---

## Documentação

Tipos de documentos utilizados:

    ARCHITECTURE
        estado arquitetural atual e vivo

    BASELINE
        fotografia de um estado específico da máquina

    ADR
        decisão arquitetural e motivação

    LAB
        experimento, procedimento e resultado

    RUNBOOK
        procedimento operacional repetível

Tipos planejados:

    POLICY
        regra que deve ser obedecida

    CONVENTIONS
        padrões de nomes, estrutura e organização

---

## Princípios arquiteturais

- o host deve permanecer mínimo;
- privilégio é exceção, não padrão;
- infraestrutura deve ser reproduzível;
- alterações importantes devem ser documentadas;
- projetos devem ser isolados por padrão;
- comunicação entre redes deve ser explícita;
- containers são descartáveis;
- dados persistentes devem ter armazenamento explícito;
- secrets não entram no Git;
- infraestrutura deve poder ser reconstruída a partir de código e documentação.

---

## Manutenção deste mapa

Este arquivo é um documento curado por humanos.

Ele descreve a arquitetura, as relações entre os componentes e as
regras que não podem ser inferidas apenas inspecionando a máquina.

Mudanças estruturais devem considerar se este documento também
precisa ser atualizado.

Futuramente, fatos observáveis do sistema poderão ser registrados
automaticamente em um inventário gerado, por exemplo:

    docs/generated/CURRENT-STATE.md

A intenção é separar:

    ARCHITECTURE.md
        → arquitetura, relações e intenção

    CURRENT-STATE.md
        → estado observado automaticamente na máquina

ADRs, LABs e baselines permanecem registros históricos e não devem
ser reescritos apenas para acompanhar o estado atual.

## Fundação de desenvolvimento Python — Fase 6

    Ubuntu host (control plane mínimo)
        ↓
    Docker rootless (daemon do usuário)
        ↓
    dev-python (docker/tools/python)
        ├── EDIT: diretório escolhido → /workspace (read-write)
        ├── TEST: diretório escolhido → /workspace (read-only)
        └── SANDBOX: /workspace temporário, sem projeto do host

Implementado com Python fixado por versão e digest; sem pacotes de aplicação.
Processos usam 0:0 no namespace rootless, que nesta máquina mapeia para
1000:1000 no host. Não é root real do Ubuntu. A medição e as limitações estão
no [ADR-0003](ADR-0003-rootless-development-identity.md) e no LAB-0004.

Todos os modos removem capabilities, bloqueiam novos privilégios, usam rootfs
read-only e tmpfs para temporários, sem socket Docker nem rede por padrão.
Limites: 256 MiB, quota de 0,5 CPU e 64 processos. Dependências temporárias e
cache ficam fora do código; dependências reproduzíveis pertencem a imagens
derivadas de cada projeto. Uso e limitações: docker/tools/python/README.md.

Desenvolvimento local privilegia interoperabilidade dos bind mounts. Produção
exige decisão própria de menor privilégio e usuário não-root quando apropriado.
SANDBOX reduz acesso ao host e não recebe o projeto; não autoriza execução
irrestrita de código hostil.

Git protege código e configuração versionados; containers são descartáveis.
Volumes podem conter estado não recuperável pelo Git: apagar um container não
é apagar seu volume, e a remoção de volumes é uma operação distinta e sensível.

`./scripts/check-dev-python` constrói e verifica esta fundação, incluindo
mapeamento UID/GID, bind mounts, persistência, modos e cgroups. O check-infra
continua somente leitura; laboratórios com criação de recursos são explícitos.

## Desenvolvimento C nativo Linux — Fase 7A

`docker/tools/c` aplica a fundação da Fase 6 a GCC, make, CMake, Ninja,
pkg-config e GDB. A base Debian Bookworm slim é fixada por tag/digest e os
pacotes por snapshot datado. Os modos EDIT, TEST e SANDBOX preservam identidade,
limites, mounts e proteções do dev-python, sem decisões novas de privilégio.

Código e artefatos duráveis ficam no bind autorizado em EDIT. TEST monta esse
projeto read-only e executa binários previamente compilados; builds temporários
podem ir para `/tmp`, cujo noexec impede executar diretamente o resultado.
SANDBOX não recebe o projeto e mantém `/workspace` em tmpfs também noexec.
GDB foi validado para símbolos/breakpoints sem executar processo depurado.
Não há volumes, devices, ferramentas embarcadas, rede de runtime nem socket.

`./scripts/check-dev-c` valida a imagem local; `--build` acrescenta o build e
requer autorização de rede. O LAB-0006 registra evidências e limitações.
A duplicação pequena do Compose é intencional nesta validação; nenhuma base
ou biblioteca compartilhada foi extraída. Os detalhes específicos de Python
(pip/venv/bytecode) e C (compilação/linkedição/GDB) continuam locais a cada tool.
