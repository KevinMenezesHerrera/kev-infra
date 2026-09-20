# Docker

Este diretório contém a infraestrutura Docker versionada do ambiente
`kev-dev`.

O Docker utilizado pelo ambiente é executado em modo rootless.

---

## Estado atual

    docker/
    ├── README.md
    └── labs/
        ├── network-basic/
        │   └── compose.yaml
        └── volume-basic/
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

Esses diretórios planejados ainda não representam serviços ou
containers existentes.

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

Os resultados estão documentados em:

    docs/LAB-0001-docker-network-volume.md

---

## Status das decisões de rede

A estratégia apresentada neste documento representa a direção atual
da arquitetura.

A convenção definitiva para redes internas, redes compartilhadas e
conectividade entre projetos será registrada em um ADR específico
após validação experimental.

Até essa decisão, exemplos como `proxy_net`, `monitoring_net` e redes
por projeto devem ser tratados como modelos conceituais, não como
infraestrutura já existente.
