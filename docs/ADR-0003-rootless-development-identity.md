# ADR-0003 — Identidade no desenvolvimento rootless com bind mounts

## Status e escopo

Aceito em 2026-09-24 para desenvolvimento local + Docker rootless + bind
mounts nesta máquina. Não é uma regra para produção.

## Contexto e problema

O host deve manipular normalmente arquivos produzidos pelas ferramentas.
UID numérico igual dentro e fora do container não implica a mesma identidade:
o user namespace traduz IDs. A hipótese foi medida antes de implementar Python.

## Evidência

`docker/labs/rootless-uid/run`, executado em 2026-09-24 com BusyBox 1.37.0:

| Processo no container | Arquivo no host | Nome no host |
| --- | --- | --- |
| UID 0, GID 0 | UID 1000, GID 1000 | kev-dev:kev-dev |
| UID 1000, GID 1000 | UID 100999, GID 100999 | UNKNOWN:UNKNOWN |

Ambos os mapas `/proc/self/{uid,gid}_map` mostraram:

```text
         0       1000          1
         1     100000      65536
```

Host: `uid=1000(kev-dev) gid=1000(kev-dev)`; subuid e subgid:
`kev-dev:100000:65536`. O diretório descartável recebeu modo 0777 somente
para permitir a escrita experimental do caso B; isso não é configuração do
projeto. Ambos os arquivos foram examinados por stat e removidos pelo host.

## Alternativas

- UID 1000 no container: produz arquivos de identidade subordinada, prejudicando
  edição normal pelo host; rejeitado como padrão neste contexto.
- ACLs ou permissões amplas no projeto: complexidade e acesso adicional sem
  necessidade; rejeitados.
- Código em volume/cópia: útil para isolamento, mas não substitui o fluxo EDIT.
- UID 0 no namespace rootless: corresponde ao usuário local medido; adotado.

## Decisão e justificativa

Usar explicitamente `0:0` em dev-python. Remover capabilities, impedir novos
privilégios e limitar mounts. Não usar socket Docker, devices ou privilégios
adicionais. O resultado confirmou a hipótese aplicável, sem contradição que
exigisse decisão humana adicional.

## Consequências e limitações

Root neste namespace não é root real do Ubuntu. Ainda pode modificar tudo que
estiver acessível em mounts graváveis: rootless não protege código autorizado
para escrita. TEST usa bind read-only; SANDBOX não monta o projeto.

A tradução depende do usuário, daemon e mapas configurados; executar novamente
o laboratório ao mudar de máquina. IDs fixos neste teste são um contrato desta
máquina, não uma abstração portátil. chmod feito pelo próprio processo também
pode dificultar edição; a decisão não impede mudanças de permissões pelo código.

Produção deve aplicar menor privilégio, preferindo usuário não-root quando
apropriado, e decidir separadamente identidade e armazenamento. SANDBOX reduz
acesso, mas não é uma fronteira suficiente para executar qualquer código hostil.
