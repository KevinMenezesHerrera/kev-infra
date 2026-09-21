# kev-dev Infrastructure

Configuração reproduzível do host Ubuntu e da infraestrutura local de desenvolvimento.

## Princípios

- Ubuntu permanece mínimo.
- Ferramentas específicas de projetos ficam em containers quando possível.
- Projetos são isolados por redes Docker próprias.
- Serviços compartilhados são explícitos.
- Infraestrutura é versionada.
- Alterações no host devem ser documentadas e reproduzíveis.
- Snap e Flatpak não fazem parte do host base atualmente.

## Estrutura

- `bootstrap/` — reconstrução e provisionamento do host
- `docs/` — arquitetura, decisões e baselines
- `docker/` — infraestrutura Docker compartilhada
- `system/` — configurações do Ubuntu
- `scripts/` — ferramentas administrativas

## Verificação local

Execute `./scripts/check-infra` para verificar Docker rootless, os serviços
systemd e o socket local, sem corrigir ou modificar o ambiente.
O script requer Bash, Docker CLI e systemctl; Git é usado apenas para relatório.
Não usa sudo nem acessa a rede.

`PASS` indica condição atendida; `FAIL` indica falha obrigatória ou impossibilidade
de verificá-la, inclusive por falta de acesso ao Docker ou ao systemd.
`WARN` informa alterações no Git ou indisponibilidade desse relatório.
O código de saída é `1` quando há `FAIL` e `0` caso contrário; um working tree
com alterações não causa falha. Execute como o usuário do Docker rootless.

Execute `./scripts/tests/check-infra-test` para rodar a suíte Bash isolada,
sem framework externo. Ela usa mocks de Docker, systemctl e Git via `PATH`,
sem consultar esses componentes do host, acessar a rede ou alterar serviços.
Os temporários são criados no repositório e removidos ao sair ou receber
INT/TERM. A consulta ao tipo do socket é substituída em memória nos cenários;
a função original também é testada com caminho ausente e arquivo regular.
A suíte não comprova a existência de um socket real: para verificar o host,
execute `./scripts/check-infra`.
