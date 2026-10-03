# LAB-0007 — Cross-compilation ARM sobre a fundação rootless

Executado em 2026-10-03, worktree
`/home/kev-dev/worktrees/kev-infra/codex-phase-7b-dev-embedded`, branch
`agent/phase-7b-dev-embedded`, base `af6438c073b5839b4a0609d52a4fb05c2111d1ad`,
inicialmente limpa. Resultado: PASS para o escopo medido.

A fundação das Fases 6/7A suporta este fixture Cortex-M3 por cross-compilation
sem aumentar privilégios, mudar limites ou relaxar noexec. Isso comprova
compilação e estrutura de artefatos; não comprova execução ou funcionamento
elétrico numa MCU. Não houve hardware, SDK, emulador, flashing ou debugging.

## Reprodução e imagem

```bash
./scripts/check-dev-embedded --config-only
# Com aprovação pontual de Docker/rede:
./scripts/check-dev-embedded --build
./scripts/check-dev-embedded
./scripts/check-infra
./scripts/tests/check-infra-test
./scripts/check-dev-c
./scripts/check-dev-python  # runner existente inclui build e requer aprovação
```

Detalhes: [tool](../docker/tools/embedded/README.md) e
[lab](../docker/labs/dev-embedded/README.md). Runner usa Python stdlib no host;
nenhum pacote instalado no Ubuntu. Config-only passou sem daemon.

Base igual à Fase 7A: Debian bookworm-20250908-slim,
`sha256:df52e55e3361a81ac1bead266f3373ee55d29aa50cf0975d440c2be3483d8ed3`.
APT autenticado nos snapshots Debian/Security `20250908T000000Z`.
Consulta apt-cache policy executada antes de fixar versões e antes das primeiras
alterações no repositório; build confirmou via APT/dpkg:

| Pacote | Versão no snapshot/build |
| --- | --- |
| gcc-arm-none-eabi | 15:12.2.rel1-1; compilador reporta 12.2.1 20221205 |
| binutils-arm-none-eabi | 2.40-2+18+b1 |
| make | 4.3-4.1 |

Dependências transitivas: libisl23/libmpc3/libmpfr6; newlib recomendada não foi
instalada (`--no-install-recommends`). São pins históricos, sem promessa de
atualização de segurança. Imagem executada Linux amd64:
`sha256:0784d272239fe2191b6e085caa4473e00e905d0c0c55fee9fda757e7e158781e`,
668 MB reportados pelo Docker.

## Resultados reais

| Verificação | Resultado observado |
| --- | --- |
| Sintaxe/config | bash -n, AST Python e Compose JSON passaram |
| Rootless | contexto/socket esperado e docker info rootless; serviços rootful disabled/inactive |
| Build | APT autenticado, versões fixadas, imagem construída |
| Arquitetura | ELF32 little-endian ARM EXEC, ARMv7-M/Microcontroller, Thumb-2 |
| Entry/vetores | entry 0x08000029, Reset_Handler 0x08000028; bit Thumb; stack 0x20005000 |
| Símbolos | main, Reset_Handler, counter, seed, _stack_top presentes; disassembly contém main |
| Seções/segmentos | vectors/text em FLASH; data em 0x20000000; bss NOBITS em 0x20000004; dois LOAD |
| Tamanho | text=104, data=4, bss=4; size total=112; BIN=108 bytes (bss não ocupa BIN) |
| Artefatos | objetos, ELF, BIN, HEX, MAP não vazios; HEX convertido a BIN coincide byte a byte |
| Debug | .debug_info preservada; nenhuma flag alterada para igualar hashes |
| EDIT | identidade 0:0, uid/gid maps 0→1000; ownership de todas as entradas 1000:1000 |
| Host/recriação | host remove artefato e edita seed 7→9; container novo recompila; BIN muda |
| TEST | escrita EROFS; build/inspeção em /tmp; conteúdo do projeto inteiro permanece igual |
| SANDBOX | compila texto do fixture sem bind; sem projeto/socket; rootfs recusa escrita |
| Proteções | inspeção de todos os containers; CapEff=0, NoNewPrivs=1, somente lo em SANDBOX |
| Tmpfs | /tmp e workspace SANDBOX noexec; arquivos/build desaparecem na recriação |
| cgroups | memory.max=268435456; cpu.max=50000 100000; pids.max=64 |
| Infra | check-infra: 0 FAIL, 1 WARN informativo por working tree alterada; check-infra-test: 10/10 cenários PASS |
| Regressões | check-dev-c e check-dev-python completos: exit 0 |
| Cleanup | containers próprios removidos por ID após label; scratches removidos; nenhum volume/rede Embedded |

## Determinismo medido

Dois builds limpos em containers distintos, mesma imagem, fonte, flags e caminhos
internos (/workspace, build), com debug, produziram SHA-256 iguais:

| Artefato | SHA-256 em ambos os builds |
| --- | --- |
| ELF | acef0d71a39d66758f6f975fb8bb9ab443334a3d8cbe967295c3e94b27caac18 |
| BIN | 9661e66f88dad4506909996b1b0e020b2deca9c7e0f74ddc59436707d493a3e2 |
| HEX | f2a8fe60b276f81c1b0429ddd8933c7a7737b3e7a4f5f051e31f1fe236a66e79 |
| MAP | 9cf45300269b21f6d314b5a341e6e0a665d29e8fe846a0884c80b3088bc9c63b |

main.o e startup.o também tiveram hashes iguais. A repetição final reproduziu
estes resultados. Após editar seed para 9, os builds em EDIT (`build`) e TEST (`/tmp/build`) deram:

| Artefato | Hash EDIT | Hash TEST |
| --- | --- | --- |
| ELF | 13d2d3ba95b41779bdb9bbfed105763b2370ceae428cc67756d754ab3db6733a | igual |
| BIN | e85f95363e6fd43463303b62149db5535f16343a0898d77c80b9fae683e134db | igual |
| HEX | fc9721bae8e747604a0eaa113ba6bcb786743f6f58fbdb061084f251c1f642e9 | igual |
| MAP | 9cf45300269b21f6d314b5a341e6e0a665d29e8fe846a0884c80b3088bc9c63b | 1419edabe33a21e1b5f63e982aa50a2b587d3b6864f15ae1e4b82baa47bce671 |

O diff real do MAP contém caminhos de objetos e OUTPUT:
`build/main.o` → `/tmp/build/main.o`, idem startup.o e firmware.elf.
Endereços, tamanhos e seções permanecem iguais; diff DWARF info vazio.
Conclusão limitada: ELF/BIN/HEX determinísticos nas condições medidas;
MAP contextual à localização de saída. Nenhuma normalização foi aplicada.
Não medimos outro caminho de fonte, toolchain, plataforma ou host; não há
promessa de determinismo universal nem de reproducibilidade do digest da imagem.

## Falhas intermediárias

1. Sandbox Codex recusou acesso ao socket rootless. Consulta/build/labs foram
   autorizados pontualmente fora do sandbox; não se alterou o host.
2. Execução `phase7b-c38c2a70c76c`: build/compilação/ELF passaram, mas objcopy
   não autodetectou HEX na conversão de volta. Correção: declarar `-I ihex`.
   Não houve alteração de firmware/flags/proteções. Um container removido.
3. `phase7b-aa4ab6fc3cde`: laboratório completo PASS, seis containers removidos.
4. `phase7b-09324a4722b0`: versão final com checks extras de vetor/BIN/cleanup,
   PASS, seis containers removidos.

Logs de trabalho estão em /tmp/phase7b-{build-lab,local-lab,final-lab}.log;
regressões em /tmp/phase7b-regression-{c,python}.log. /tmp não é registro durável.
Os resultados acima e comandos reproduzíveis são o registro versionável.

## Recursos finais e limites

Auditoria final: zero containers, zero volumes, redes padrão com IDs preservados:
bridge feaf10d8cd26, host 9faba7affe3d, none c3e0f5392b43.
Nenhum inventário completo foi capturado antes do primeiro build; a primeira
consulta de recursos ocorreu após o build inicial, e também tinha zero
containers/volumes e estas redes. Não se presume um baseline anterior não medido.

Permanecem dev-embedded (668 MB), imagem sem tag da consulta ao snapshot
`efef71fb9e0b` (148 MB), cache/camadas e imagens preexistentes dev-c, dev-python,
Python, BusyBox e hello-world. Nada foi apagado por prune.
A regressão Python refez a referência local dev-python: digest anterior
5b60878cfc94… → 8f3b5bab87d3…; nenhum pacote ou configuração da Fase 6 mudou.
Regressão C `phase7a-3d46a66359f2` removeu seus cinco containers;
Python `phase6-86ce76329526` removeu containers/volume próprios, incluindo LAB UID.
Scratch Embedded removido; diretório de consulta /tmp/phase7b-package-probe e
logs de trabalho permanecem como evidências locais.

Não executados: hardware, emulação, flashing/debugging, OOM/saturação de PIDs,
projetos grandes, outras arquiteturas/plataformas e builds em caminhos de fonte
distintos. Limites foram lidos nos cgroups; não são medidas de pico de consumo.
Mapa FLASH/RAM e tabela de reset são didáticos; não representam placa nem
vetor completo de interrupts. A igualdade BIN/HEX valida conversão do formato,
não inicialização real. Nenhum teste de execução ARM foi realizado.

## Comparação Python / C / Embedded

| Grupo | Python | C | Embedded |
| --- | --- | --- | --- |
| 1. Comprovadamente comuns | rootless, identidade, EDIT rw/TEST ro/SANDBOX sem projeto, caps/rootfs/rede/limites | mesmas propriedades, regressão real | mesmas propriedades, inspeção/config/runtime reais |
| 2. Específicas da toolchain | interpretação, pip/venv/bytecode; persistência em volume no lab | GCC Linux, Make/CMake/Ninja, binários nativos, GDB símbolos | GCC ARM, startup/linker, ELF/BIN/HEX/MAP, inspeção cross, sem libc |
| 3. Semelhantes, inseguras para abstração | Compose e runner; inclui build no fluxo padrão | Compose e runner, offline padrão; execução afetada por noexec | Compose e runner, offline padrão; cross artefatos são dados, hashes contextuais |
| 4. Necessidades novas Embedded | não medidas como requisito aqui | não medidas como requisito aqui | mapa didático e vetores, distinção host/alvo, debug e hashes por contexto; nenhum novo privilégio/recurso |

Não há equivalência artificial: Python interpreta, C executa binários do bind,
Embedded somente compila/inspeciona e por isso consegue completar builds noexec
em TEST/SANDBOX sem executar o resultado. CMake/cross try_run não foi testado.

Recomendação: uma fase posterior pode avaliar uma extração estreita das regras
Compose e checks de segurança com regressões dos três ambientes. Manter locais
os cenários, política build/offline, dependências e artefatos. Três casos dão
evidência de repetição, mas não justificam ainda imagem base ou framework comum.
Nenhuma abstração ou novo ADR foi introduzido nesta fase; ADRs/LABs/baselines
anteriores permanecem intactos. Nenhum git add/commit/merge/push foi executado.
