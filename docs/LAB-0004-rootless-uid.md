# LAB-0004 — Mapeamento UID/GID rootless

Executado em 2026-09-24. Resultado: PASS.

## Preflight

Worktree `/home/kev-dev/worktrees/kev-infra/phase-6-dev-python`, branch
`agent/phase-6-dev-python`, inicialmente limpa. `./scripts/check-infra`:
0 FAIL, 0 WARN fora do sandbox. A primeira tentativa restrita não conseguiu
consultar Docker/systemd (5 FAIL) e foi interrompida; retomada autorizada.
Docker client/server 29.8.0; Compose 5.5.1; contexto rootless;
socket `/run/user/1000/docker.sock`; systemd cgroup v2.
Docker/containerd do sistema disabled/inactive; Docker do usuário active.

Inventário inicial: zero containers, zero volumes; redes bridge, host e none;
imagens busybox:1.37.0 e hello-world:latest.

## Hipótese e procedimento reproduzível

UID 0 no namespace deve corresponder ao usuário do daemon; UID 1000 pode
corresponder a uma identidade subordinada. Execute:

```bash
./docker/labs/rootless-uid/run
```

O script executa check-infra, id, consulta subuid/subgid e cria diretório único
na worktree, sem dados de projeto. Dois containers BusyBox locais, sem rede,
criam arquivos com identidades 0:0 e 1000:1000; id e mapas são impressos.
stat no host observa ambos. Remoção é limitada aos dois arquivos e ao diretório
criado por mktemp; containers são removidos por --rm.

## Observações

- Host fora do sandbox: uid=1000(kev-dev), gid=1000(kev-dev), grupos
  1000(kev-dev), 27(sudo), 100(users). Nenhum sudo foi executado.
- `/etc/subuid` e `/etc/subgid`: `kev-dev:100000:65536`.
- Container A: uid=0(root), gid=0(root), groups=0(root).
- Container B: uid=1000, gid=1000, groups=1000.
- Arquivo A: uid=1000 gid=1000 owner=kev-dev group=kev-dev.
- Arquivo B: uid=100999 gid=100999 owner=UNKNOWN group=UNKNOWN.
- Ambos os mapas: `0 1000 1` e `1 100000 65536`.
- Assertions passaram; diretório temporário removido.

Decisão: [ADR-0003](ADR-0003-rootless-development-identity.md).
