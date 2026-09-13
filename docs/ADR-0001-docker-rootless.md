# ADR-0001 — Docker Rootless como engine principal

## Status

Aceito.

## Contexto

O host Ubuntu deve permanecer mínimo, organizado e com privilégio reduzido.

Containers serão usados para:

- ambientes de desenvolvimento;
- serviços de projetos;
- bancos de dados;
- ferramentas;
- testes de comunicação entre serviços.

O host também poderá futuramente trabalhar com hardware e ambientes que exijam privilégios adicionais.

## Decisão

Usar Docker Engine em modo rootless como engine principal de desenvolvimento.

O daemon rootful do sistema não será utilizado por padrão.

## Estado implementado

- Docker Engine: 29.8.0
- Docker Compose: 5.5.1
- Buildx: 0.37.1
- cgroup: v2
- storage driver: overlayfs
- Docker root dir: /home/kev-dev/.local/share/docker
- socket rootless: /run/user/1000/docker.sock
- contexto CLI ativo: rootless

Serviços rootful desativados:

- docker.service
- docker.socket
- containerd.service

Serviço utilizado:

- systemd --user docker.service

O usuário kev-dev não foi adicionado ao grupo docker.

Linger não foi habilitado.

## Motivação

O modo rootless reduz os privilégios do daemon Docker e dos containers em relação ao host.

A opção rootful com usuário no grupo docker foi rejeitada como padrão porque acesso ao socket de um daemon rootful representa, na prática, uma fronteira de privilégio comparável a acesso root.

## Consequências

Vantagens:

- menor superfície privilegiada;
- isolamento melhor entre containers e host;
- não exige sudo para operações Docker comuns;
- dados Docker pertencem ao ambiente do usuário.

Limitações:

- algumas operações de rede avançadas podem ter comportamento diferente;
- acesso a USB, JTAG, serial e outros devices pode exigir solução específica;
- containers privilegiados e integrações de baixo nível não devem ser presumidos;
- certos limites de I/O via cgroup não estão disponíveis no ambiente atual.

## Regra

Privilégio deve ser exceção, não padrão.

Caso um projeto futuro necessite de recursos incompatíveis com rootless, essa necessidade deverá ser tratada separadamente e documentada, em vez de transformar todo o ambiente Docker em rootful.
