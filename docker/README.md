# Docker

Este diretório contém a infraestrutura Docker versionada do ambiente
`kev-dev`.

O Docker utilizado pelo ambiente é executado em modo rootless.

---

## Estado atual

    docker/
    ├── README.md
    ├── tools/c/
    ├── tools/python/
    │   ├── Dockerfile
    │   ├── compose.yaml
    │   └── README.md
    └── labs/
        ├── rootless-uid/
        ├── dev-python/
        ├── dev-c/
        ├── network-basic/
        │   └── compose.yaml
        ├── volume-basic/
        │   └── compose.yaml
        └── shared-network/
            ├── project-a/
            │   └── compose.yaml
            └── project-b/
                └── compose.yaml

Os laboratórios existentes servem para validar propriedades da
infraestrutura antes que essas propriedades sejam adotadas na
arquitetura permanente.

---

## Estrutura planejada

A estrutura poderá evoluir aproximadamente para:

    docker/
    ├── labs/
    │
    ├── tools/
    │   ├── python/
    │   ├── c/
    │   └── embedded/
    │
    └── services/
        └── ...

tools/python e tools/c já estão implementados. Os demais diretórios planejados ainda
não representam serviços ou containers existentes.

Eles só devem ser criados quando houver implementação correspondente.

---

## Responsabilidade dos mecanismos

Cada mecanismo possui uma responsabilidade diferente:

    imagem / container
        → executáveis, processos e ferramentas

    bind mount / volume
        → arquivos e dados

    rede
        → comunicação entre processos

    secret
        → credenciais e material sensível

Uma rede não disponibiliza automaticamente executáveis ou bibliotecas
de um container para outro.

---

## Containers de ferramentas

Ambientes como Python, C ou desenvolvimento embarcado devem ser
tratados como ambientes de execução.

Exemplo:

    projeto no host
          │
          │ bind mount
          ▼
    dev-python
          │
          ├── python
          ├── pip
          └── pytest

Outro ambiente pode montar o mesmo projeto:

    projeto
       ├── dev-python
       └── dev-c

A rede é utilizada apenas quando esses containers precisam se
comunicar com serviços.

---

## Estratégia de redes

O padrão é isolamento.

Não deve existir uma rede global na qual todos os containers sejam
colocados automaticamente.

A direção arquitetural é:

    redes internas por projeto
        +
    redes compartilhadas por finalidade
        +
    conexão explícita entre containers e redes

Exemplos conceituais:

    brsa_internal

    metra_internal

    proxy_net

    monitoring_net

Um container pode pertencer a múltiplas redes quando necessário.

Essa associação deve ser intencional.

---

## Persistência

Containers são descartáveis.

Dados que precisam sobreviver à destruição de um container devem usar:

- volumes nomeados; ou
- bind mounts explicitamente definidos.

O diretório interno de armazenamento do Docker não deve ser manipulado
manualmente como mecanismo normal de persistência.

---

## Laboratórios

### network-basic

Valida:

- DNS interno do Docker;
- comunicação dentro da mesma rede;
- isolamento entre redes;
- conexão e desconexão dinâmica entre redes.

### volume-basic

Valida:

- criação de volume nomeado;
- persistência após remoção do container;
- reutilização do volume por um container recriado.

### shared-network

Valida:

- uso de uma rede `external: true`;
- compartilhamento da mesma rede por projetos Compose independentes;
- comunicação por DNS e HTTP entre os projetos;
- independência do ciclo de vida dos projetos;
- preservação da rede após `docker compose down`;
- recusa de remoção da rede enquanto existirem endpoints ativos;
- remoção explícita da rede quando não estiver mais em uso.

Os resultados estão documentados em:

    docs/LAB-0001-docker-network-volume.md
    docs/LAB-0002-shared-external-network.md

---

## Status das decisões de rede

A estratégia de segmentação de redes foi formalizada no:

    docs/ADR-0002-docker-network-strategy.md

O mecanismo de rede externa compartilhada entre projetos Compose
independentes foi validado experimentalmente no LAB-0002.

Exemplos como `proxy_net`, `monitoring_net` e outras redes
compartilhadas por finalidade continuam sendo modelos conceituais até
que exista uma necessidade real de implementação.

## Fase 6 implementada

- `tools/python/`: Dockerfile fixado, Compose EDIT/TEST/SANDBOX e instruções.
- `labs/rootless-uid/`: medição empírica antes da escolha de identidade.
- `labs/dev-python/`: bind mounts, persistência, modos e limites de recursos.
- `../scripts/check-dev-python`: validação integrada com build e laboratórios.

Os diretórios `tools/python` e `tools/c` já existem; embedded e services continuam planejados.
A identidade 0:0 no desenvolvimento rootless mapeia nesta máquina para o usuário
1000:1000 do host (ADR-0003); não é recomendação automática para produção.
Os resultados estão nos LAB-0004 e LAB-0005. Consulte o README de tools/python
para comandos e a separação entre código, dependências e caches temporários.

## Fase 7A — C nativo Linux

- `tools/c/`: Debian por tag/digest e pacotes de snapshot fixo; GCC, make,
  CMake, Ninja, pkg-config e GDB. Mesmos modos e proteções de dev-python.
- `labs/dev-c/` e `../scripts/check-dev-c`: compilação, execução, ownership,
  interação host/container, GDB para símbolos/breakpoints, sem run/attach, isolamento e cgroups.
- `../docs/LAB-0006-dev-c.md`: resultados, limites e comparação arquitetural.

O build requer autorização de rede; verificações posteriores podem usar somente
imagem local. Não há volumes ou camada compartilhada entre as ferramentas.
Tmpfs mantém noexec: execução de binários compilados foi validada no bind EDIT
ou TEST, não em tmpfs. Uso: [tools/c/README.md](tools/c/README.md).
