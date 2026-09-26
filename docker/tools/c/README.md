# C nativo Linux de desenvolvimento

GCC, make, CMake, Ninja, pkg-config e GDB para projetos C nativos Linux.
Sem toolchain embarcada, cross-compiler, devices, socket Docker ou volumes.
`libc6-dev` fornece headers e arquivos de ligação necessários para C; os demais
pacotes transitivos são dependências das ferramentas solicitadas. Não há
instalação de ferramentas no host.

## Imagem e reprodução

Base oficial `debian:bookworm-20250908-slim`, fixada pelo digest do índice
`sha256:df52e55e3361a81ac1bead266f3373ee55d29aa50cf0975d440c2be3483d8ed3`.
Bookworm mantém a família Debian já usada no dev-python, sem incluir um
interpretador de aplicação como base da toolchain C. APT usa exclusivamente
snapshots Debian e Debian Security em `20250908T000000Z`: isso fixa também
a resolução das dependências, que um digest da base sozinho não fixaria.

Os índices assinados e hashes dos pacotes continuam verificados. Somente
`Valid-Until` é desabilitado para ler o arquivo histórico. O transporte HTTP
não fornece confidencialidade; autenticidade é verificada pelo APT com o
keyring Debian da base. Nenhum download é executado diretamente por shell.
Os pins são uma escolha reproduzível, não uma afirmação de atualização de
segurança. Atualizar base/snapshot requer revisão e nova execução do laboratório.
A reprodução fixa as entradas; não promete digest final idêntico bit a bit
entre builds com metadados/proveniência diferentes.

Na raiz da worktree, após aprovação de rede para o build:

```bash
./scripts/check-infra
docker --context rootless compose -f docker/tools/c/compose.yaml build sandbox
```

## Modos

Defina `DEV_WORKSPACE` como caminho absoluto do projeto autorizado. Sem a
variável, Compose usa o diretório desta ferramenta. Não selecione `/`, `/home`,
o home inteiro nem diretórios com secrets.

```bash
# EDIT: fonte no host, artefato gravado no projeto e executado no container.
DEV_WORKSPACE="$PWD/meu-projeto" docker --context rootless compose -f docker/tools/c/compose.yaml run --rm --pull never edit sh -ec 'gcc -Wall -Wextra -g main.c -o hello && ./hello'
# TEST: executa o binário já compilado no projeto read-only.
DEV_WORKSPACE="$PWD/meu-projeto" docker --context rootless compose -f docker/tools/c/compose.yaml run --rm --pull never test ./hello
# SANDBOX: sem projeto do host; workspace descartável.
docker --context rootless compose -f docker/tools/c/compose.yaml run --rm --pull never sandbox gcc --version
```

Todos os modos mantêm `0:0` conforme ADR-0003 (1000:1000 no host medido),
rootfs read-only, rede none, cap_drop ALL, no-new-privileges, memória 256 MiB,
0,5 CPU, 64 processos e `/tmp` tmpfs de 64 MiB. SANDBOX acrescenta `/workspace`
tmpfs de 64 MiB. Nenhuma exceção de seccomp ou capability foi adicionada.
Essa identidade é exclusiva ao desenvolvimento local rootless, sem definir
política de produção.

C escreve objetos, executáveis e arquivos de configuração de build. Em EDIT,
use um diretório de build no projeto. Em TEST, `cmake -S /workspace -B /tmp/build
-G Ninja` seguido de `cmake --build /tmp/build --parallel 1` permite compilar
sem escrever no código. Porém os tmpfs padrão são **noexec**: executar o novo
binário diretamente ali é recusado. Isso também limita execução de binários
criados em SANDBOX e projetos CMake que usam `try_run`. Para executar testes,
compile antes em EDIT e execute o artefato em TEST. Habilitar execução em tmpfs
exigiria uma decisão separada; esta implementação mantém as proteções da Fase 6.

GDB foi validado carregando símbolos e definindo/listando breakpoint com
`-nx -nh -batch -iex 'set auto-load off'`. Não foi testado `run`, attach ou
ptrace de outro processo; não se afirma suporte a essas operações. Se forem
necessárias e bloqueadas, pare para decisão antes de alterar capabilities,
seccomp ou outras proteções.

Use builds sequenciais inicialmente. Os limites atendem o projeto mínimo
medido, sem garantir capacidade para projetos grandes. Não há cache persistente
que justifique volumes nesta versão. Rede de runtime permanece desabilitada;
dependências adicionais pertencem a imagens deliberadamente derivadas.

## Validação

```bash
./scripts/check-dev-c --config-only  # sem daemon; JSON e proteções
./scripts/check-dev-c               # imagem local, sem build/pull
./scripts/check-dev-c --build       # build + lab; requer autorização de rede
```

O build é explícito para não iniciar downloads durante uma verificação offline.
Procedimento: [laboratório](../../labs/dev-c/README.md).
Resultados e comparação com Python: [LAB-0006](../../../docs/LAB-0006-dev-c.md).
