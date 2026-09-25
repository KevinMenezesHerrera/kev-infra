# Python de desenvolvimento

Base oficial Python 3.13.7 slim-bookworm fixada também por digest. Não se
pretende indicar a versão mais recente: atualizações de segurança exigem
revisão deliberada do pin e nova validação. Nenhum pacote adicional instalado.
`/workspace` recebe somente o diretório escolhido, nunca socket Docker.
Identidade `0:0` conforme ADR-0003, exclusiva ao desenvolvimento rootless.

A partir da raiz desta worktree, com contexto rootless verificado:

```bash
./scripts/check-infra
docker --context rootless compose -f docker/tools/python/compose.yaml build sandbox
DEV_WORKSPACE="$PWD" docker --context rootless compose -f docker/tools/python/compose.yaml run --rm edit python --version
DEV_WORKSPACE="$PWD" docker --context rootless compose -f docker/tools/python/compose.yaml run --rm test python -m unittest discover
docker --context rootless compose -f docker/tools/python/compose.yaml run --rm sandbox python -c 'print("sandbox")'
```

Defina DEV_WORKSPACE explicitamente para EDIT e TEST como caminho absoluto do
projeto autorizado. Sem a variável, Compose usa este diretório de ferramentas.
Não use `/`, `/home`, o home do usuário ou diretórios com secrets. EDIT permite
escrever no projeto inteiro escolhido; TEST monta-o read-only. SANDBOX não tem
bind nem volume persistente. Nenhuma porta ou rede é fornecida por padrão.

Todos os modos: 256 MiB de memória, quota de 0,5 CPU, 64 processos, rootfs
read-only, cap_drop ALL, no-new-privileges, /tmp em tmpfs de 64 MiB. SANDBOX
acrescenta /workspace em tmpfs de 64 MiB. Quota de CPU não altera necessariamente
o número retornado por os.cpu_count(); a fonte é cpu.max do cgroup.

Cache pip em /tmp/pip-cache e bytecode desabilitado evitam escrever no código.
Para dependências temporárias, `python -m venv /tmp/venv` separa ambiente e código;
é descartado com o container. Para dependências duráveis e testes offline,
derive uma imagem com dependências fixadas por projeto; não instale toolchains
no host. Esta fundação não inclui pytest, compilador ou dependências de apps.
A rede desabilitada impede downloads em runtime; conectividade futura exige
configuração explícita por projeto. O tmpfs limita venvs grandes; dimensione
conscientemente ou use imagem derivada, sem tornar o projeto gravável no TEST.

Validação completa (cria e remove somente recursos experimentais identificados):

```bash
./scripts/check-dev-python
```

Git preserva código/configuração versionados. Container é descartável; volume
pode conter dados não recuperáveis pelo Git. Remover containers e remover volumes
são operações distintas. O laboratório apaga apenas o volume que ele próprio
criou, após verificar seu label; não use prune para limpeza.
