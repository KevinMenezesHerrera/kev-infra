# Laboratório dev-c

Execute na raiz da worktree:

```bash
./scripts/check-dev-c --config-only
./scripts/check-dev-c --build
./scripts/check-dev-c
```

`--build` permite baixar a base e pacotes fixados e requer aprovação de rede.
Sem essa opção, a imagem deve existir localmente; o laboratório usa `--pull never`.
O entrypoint `python3 docker/labs/dev-c/run.py` aceita as mesmas opções e executa
seu próprio preflight. Python 3 stdlib já existe no control plane e permite ler
JSON, verificar ownership e controlar cleanup sem jq ou pacotes adicionais.
Não depende do interpretador da imagem dev-python e não instala nada no host.

O preflight executa check-infra e exige host 1000:1000. O Compose é validado
estruturalmente, seguido por inspeção efetiva de cada container. O teste cria
fontes e Makefile/CMakeLists no host e verifica:

1. Versões de GCC, make, CMake, Ninja, pkg-config e GDB.
2. GCC e execução com resultado conhecido; Make; CMake/Make; CMake/Ninja.
3. Símbolos de debug e breakpoint no GDB em batch, sem iniciar processo depurado.
4. Ownership 1000:1000 de fontes/artefatos/subdiretórios; edição e remoção pelo host.
5. Recriação de EDIT após edição da fonte no host; persistência do código e builds.
6. TEST read-only: escrita rejeitada, binário do bind executável e build em `/tmp`.
   tmpfs noexec é verificado, inclusive recusa de execução do binário novo.
7. SANDBOX sem bind/volume/socket/projeto, rootfs read-only, CapEff=0,
   NoNewPrivs=1, rede none com somente loopback, tmpfs descartado na recriação.
8. cgroups: memory.max=268435456, cpu.max com quota/período=0,5, pids.max=64.

Build e experimentos são separados para que novas execuções possam ser offline.
Um lab completo usa cinco containers, sem criar volumes ou redes. Nomes e label
Compose usam identificador aleatório `phase7a-*`. Cleanup verifica o label de
posse antes de remover um container e apaga apenas seu scratch único sob este
diretório. Falhas normais também fazem cleanup; SIGKILL pode deixar recursos.
Nesse caso, inspecione o identificador e labels antes de remover qualquer coisa.
Nunca use prune. Imagem e cache de build permanecem deliberadamente.

O sandbox do agente pode bloquear socket e buses: nesse caso solicite acesso
específico, sem interpretar o bloqueio como defeito da infraestrutura.

Limites: não mede OOM/saturação de processos, não valida depuração de processo,
não executa binários novos em tmpfs noexec, nem testa projetos grandes.
Resultado histórico: [LAB-0006](../../../docs/LAB-0006-dev-c.md).
