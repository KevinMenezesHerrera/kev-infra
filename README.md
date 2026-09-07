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
