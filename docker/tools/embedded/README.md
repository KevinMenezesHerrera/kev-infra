# dev-embedded — Cortex-M3 sem hardware

Toolchain GNU ARM bare-metal em Docker rootless. Não executa firmware.
Base Debian `bookworm-20250908-slim` por digest (ver Dockerfile); APT autenticado
nos snapshots Debian/Security `20250908T000000Z`. Consulta real ao snapshot
confirmou gcc-arm-none-eabi `15:12.2.rel1-1`, binutils-arm-none-eabi
`2.40-2+18+b1` e make `4.3-4.1`; o build confirmou os mesmos pacotes.
São pins históricos, não uma declaração de segurança atual. Atualizar exige
revisão e repetição do laboratório. Dependências transitivas observadas:
libisl23, libmpc3 e libmpfr6. Sem newlib/libc de alvo, C++, SDK ou depurador.

## Modos e uso

```bash
./scripts/check-dev-embedded --config-only
# Após autorização específica de Docker/rede:
./scripts/check-dev-embedded --build
# Imagem local obrigatória; --pull never:
./scripts/check-dev-embedded

# Projeto escolhido explicitamente, caminho absoluto existente:
DEV_WORKSPACE=/caminho/absoluto/projeto docker --context rootless compose \
  -f docker/tools/embedded/compose.yaml --profile edit run --rm --pull never edit make -j1
```

EDIT monta o projeto rw; TEST ro; SANDBOX não monta dados do host.
Identidade interna 0:0 mapeia neste host para 1000:1000 (ADR-0003).
Todos usam rootfs read-only, cap_drop ALL, no-new-privileges, rede none,
256 MiB, 0,5 CPU e 64 PIDs. `/tmp` é tmpfs de 64 MiB; SANDBOX também tem
`/workspace` tmpfs de 64 MiB. Docker mantém noexec; não adicionar exec.
Sem volumes, devices, sockets, USB, serial ou privilégios adicionais.
Build é a única etapa com rede; a execução normal não faz downloads.

## Fixture didático

[Fixture](../../labs/dev-embedded/fixture/) contém main.c, startup.S, linker.ld
e Makefile. FLASH: 0x08000000/64 KiB; RAM: 0x20000000/20 KiB. Esse mapa não
representa uma placa específica. A tabela mínima contém somente stack/reset;
não é um vetor completo de interrupções para produção. Startup copia `.data`,
zera `.bss` e chama main. O programa altera um contador volátil em loop.

Flags: Cortex-M3/Thumb, `-g -O0 -ffreestanding`, warnings como erros;
link `-nostdlib`. Sem remover debug ou normalizar caminhos para igualar hashes.
`make -j1` produz objetos, ELF, BIN, HEX e MAP em build;
`make -j1 OUT=/tmp/build` permite build temporário em TEST.
Ferramentas cross executam no container; artefatos ARM são dados inspecionados.
Noexec não impede compilar ou ler arquivos e não precisa ser relaxado.

Inspeção de ELF/BIN/HEX comprova cross-compilation e estrutura, não funcionamento
elétrico, inicialização real ou execução numa MCU. Nenhum hardware, emulador,
flashing ou debugging físico foi usado. Resultados e limites:
[LAB-0007](../../../docs/LAB-0007-dev-embedded.md).
