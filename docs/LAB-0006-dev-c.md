# LAB-0006 — C nativo Linux sobre a fundação da Fase 6

Executado em 2026-09-26 na worktree `phase-7-dev-c`, branch
`agent/phase-7-dev-c`, inicialmente limpa. Resultado final: PASS para o escopo
abaixo, com o limite noexec preservado. Nenhuma decisão da Fase 6 foi alterada.

## Hipótese e reprodução

Identidade, mounts, modos, isolamento e recursos de dev-python devem servir
para desenvolvimento C nativo sem base comum nem aumento de privilégio.

```bash
./scripts/check-dev-c --config-only
# Com aprovação de rede restrita à base e aos snapshots do Dockerfile:
./scripts/check-dev-c --build
# Repetição com imagem local, sem build/pull:
./scripts/check-dev-c
./scripts/check-infra
./scripts/tests/check-infra-test
./scripts/check-dev-python
```

A regressão Python tem seu próprio build e precisa da aprovação correspondente.
Procedimento detalhado e cleanup: [README do lab](../docker/labs/dev-c/README.md).
Python stdlib no host mantém o padrão existente e evita dependências como jq;
a toolchain C fica inteiramente no container.

## Imagem

Debian oficial `bookworm-20250908-slim`, índice
`sha256:df52e55e3361a81ac1bead266f3373ee55d29aa50cf0975d440c2be3483d8ed3`,
consultado no registro antes do build. A plataforma executada foi Linux amd64.
Pacotes resolvidos exclusivamente nos snapshots Debian e Debian Security de
`20250908T000000Z`, com assinaturas e hashes verificados pelo APT.

Bookworm mantém a família Debian do Python sem usar Python como imagem base.
`libc6-dev` é necessário para headers e ligação C. Não foram adicionados
compilador C++, SDK, cross-compiler, OpenOCD ou ferramentas de aplicação.
Detalhes de reprodução e atualização: [README da tool](../docker/tools/c/README.md).

## Resultados observados

| Verificação | Resultado real |
| --- | --- |
| Sintaxe | `bash -n scripts/check-dev-c` e parse AST Python: PASS |
| Compose | `config --format json`, três modos, validação estrutural: PASS |
| Build | Dois builds concluídos; segundo reutilizou camadas em cache |
| GCC | 12.2.0; compilação com warnings como erros e execução com saída esperada |
| make | 4.3; Makefile mínimo compilou e executou |
| CMake | 3.25.1; geradores Unix Makefiles e Ninja compilaram e executaram |
| Ninja | 1.11.1; compilação e link concluídos |
| pkg-config | 1.8.1 reportado |
| GDB | 13.1; símbolo main carregado, breakpoint definido/listado em main.c:2 |
| Identidade | Processo 0:0; mapas `0 1000 1` / `1 100000 65536` |
| Ownership | 64 entradas de fontes, builds e subdiretórios: todas 1000:1000 |
| Host ↔ container | Fonte host-v1 compilada; host editou/removeu artefato; fonte host-v2 recompilada |
| Recriação | Código host-v2 e build anterior preservados após remoção do container |
| TEST | Binário do bind executou; escrita recusada com Read-only file system |
| Build TEST | CMake/Ninja em /tmp compilou; execução recusada pelo tmpfs noexec |
| SANDBOX | Sem binds/volumes, projeto ou sockets; rootfs recusou escrita |
| Proteções | Inspeção Docker e processo: CapEff=0, NoNewPrivs=1, network none, somente lo |
| tmpfs | /tmp e /workspace noexec; arquivos transitórios ausentes após recriação |
| Memória | memory.max=268435456 |
| CPU | cpu.max=50000 100000, equivalente a 0,5 CPU |
| Processos | pids.max=64 |
| check-infra | Fora do sandbox: 0 FAIL, 1 WARN informativo por mudanças Git |
| check-infra-test | Todos os 10 testes passaram |
| Regressão Python | check-dev-python completo passou, incluindo UID/GID, modos, volumes e build |
| check-dev-c | Execução local e execução integrada --build passaram |
| Git | diff --check passou; staging vazio; arquivos Python preexistentes intactos |
| Cleanup | Zero containers e volumes; redes padrão preservadas; scratch removido |

## Falhas intermediárias e limites

O sandbox bloqueou consulta ao socket rootless e aos buses, produzindo cinco
falhas de preflight. Com aprovação específica fora do sandbox, a infraestrutura
passou; esses bloqueios não foram tratados como falha do host.

A primeira tentativa de laboratório usou indevidamente `compose run --no-build`,
opção ausente no Compose instalado. Foi corrigida após consultar o help;
nenhum container foi criado nessa tentativa. O script verifica a imagem local
e usa `--pull never`; build é uma etapa explícita com `--build` no wrapper.

A tentativa seguinte chegou ao TEST e compilou com sucesso, mas a expectativa
de executar em `/tmp` estava errada: Docker monta tmpfs noexec. O laboratório
foi corrigido para medir e preservar essa proteção; não houve alteração dos
mounts. TEST executa binários previamente compilados no bind. SANDBOX também
tem workspace noexec, limitando a execução direta de novos binários e usos de
CMake `try_run`. Nenhuma solução para contornar noexec foi aplicada.

GDB só carregou símbolos e definiu/listou breakpoint, sem iniciar processo.
Não há evidência de sucesso ou bloqueio de run/attach/ptrace neste laboratório.
Uma necessidade futura de depuração real deve ser medida e, caso bloqueada,
submetida à decisão antes de alterar capabilities, seccomp ou privilégios.

Os limites de memória/CPU/processos foram lidos nos cgroups; não foi provocado
OOM nem saturação de PIDs. Projetos mínimos usaram builds sequenciais. Pins
históricos não significam pacotes atualizados; atualizar exige nova revisão.

## Recursos e limpeza

Inventário inicial: zero containers/volumes, redes bridge/host/none e imagens
BusyBox 1.37.0, hello-world:latest, Python 3.13.7-slim-bookworm e dev-python.
A imagem hello-world preexistente não foi usada.

Execuções C:

- `phase7a-38f8d45ad711`: opção inválida, zero containers.
- `phase7a-03711a57061d`: três containers, parada no noexec; todos removidos.
- `phase7a-e28eb9fe27d6`: cinco containers, PASS, todos removidos.
- `phase7a-18fcf3ab5e23`: build integrado e cinco containers, PASS, todos removidos.

Nenhum volume ou rede criado por dev-c. A regressão Python
`phase6-3d0067b737e1` criou/removeu seus sete containers e o volume
`phase6-3d0067b737e1-data`; o teste UID criou/removeu outros dois containers.
Todos os scratches foram removidos. Não foi executado prune.

Inventário final: zero containers, zero volumes, somente redes bridge, host e
none, com os mesmos IDs iniciais. Permanecem as quatro imagens nomeadas
preexistentes e `kev-infra/dev-c:bookworm-20250908` (574 MB reportados pelo Docker).
O build de regressão atualizou a referência local dev-python; nenhuma imagem
preexistente foi removida. Cache de build e camadas baixadas permanecem.
Imagem dev-c final reportada:
`sha256:d259a00ee82753bf60cbc1d6778a6d18b799c6615af8e3cc5b1f1da2aef53883`.

## Comparação e recomendação de abstração

| Aspecto | Comum | Específico |
| --- | --- | --- |
| Runtime | UID/GID, limites, rede none, rootfs read-only, caps, no-new-privileges | Imagem/tag |
| Armazenamento | EDIT rw, TEST ro, SANDBOX tmpfs, /tmp temporário | C gera objetos/binários; Python trata pip/venv/bytecode |
| Build de imagem | Base por tag/digest e contexto mínimo | C instala toolchain via snapshots; Python usa interpretador pronto |
| Laboratório | Python stdlib, Compose JSON, inspeção runtime, ownership, recriação, cleanup por posse | C testa compiladores/build systems/GDB/noexec; Python testa venv/cache e persistência em volume |
| Check | Preflight rootless e execução explícita de laboratório | C permite repetir offline por padrão; Python inclui build e LAB-0004 |

Os Compose têm 42 linhas cada: 41 idênticas na mesma posição, uma diferença
na imagem/tag. `.dockerignore` é idêntico, com duas linhas. Há repetição nos
helpers de subprocess/JSON e nas verificações de runtime/cleanup dos labs;
os cenários e recursos necessários são diferentes. Não há imagem/base ou
biblioteca compartilhada adicionada.

A evidência sustenta reutilizar os **princípios** da Fase 6. Recomenda-se manter
por enquanto os arquivos explícitos: o Compose duplicado é pequeno e a
necessidade de execução de binários versus interpretação já revelou um limite
que precisa continuar visível. Dois ambientes não demonstram ainda necessidade
de uma base comum de imagem ou framework de laboratório. Se novas ferramentas
trouxerem manutenção repetida das mesmas regras, propor uma extração estreita
para revisão antes de implementá-la. Nenhum ADR novo foi necessário.
