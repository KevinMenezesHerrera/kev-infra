# Laboratório dev-python

Execute `./scripts/check-dev-python` na raiz da worktree. Requer Docker rootless,
Compose, Python 3 stdlib já disponível no host e BusyBox 1.37.0 local (o teste de
UID usa `--pull never`). Se necessário, obtenha a imagem BusyBox explicitamente
antes de executar; o laboratório não instala pacotes no host.

O comando verifica infraestrutura, executa LAB-0004, valida JSON dos Compose
versionados, constrói a imagem fixada e executa os experimentos:

1. Bind: host escreve/container lê; container escreve/host lê, edita e remove;
   subdiretórios; stat; remoção/recriação e persistência.
2. TEST: leitura funciona, escrita deve retornar EROFS.
3. SANDBOX: ausência do projeto e sockets; rootfs read-only; tmpfs transitórios;
   capabilities efetivas zeradas e NoNewPrivs=1.
4. Recursos: memory.max=268435456, cpu.max=50000 100000; alocação de 8 MiB e
   carga de uma thread por 1,5 s para observar throttling, sem testar OOM.
5. Armazenamento: volume nomeado preserva dado entre dois containers removidos;
   arquivo da camada gravável desaparece. Somente este teste permite rootfs
   gravável, pois essa camada é justamente o objeto da medição.

Dados ficam em scratch único sob este diretório. Containers Compose usam nome
aleatório phase6-* e label de projeto; containers de armazenamento e volume usam
label kev-infra.lab. Antes de remover, o script verifica posse pelo identificador
da execução. Não há redes novas. O volume é removido em operação separada após
inspeção de label; recursos preexistentes nunca são selecionados para limpeza.

Em caso de interrupção abrupta, recursos podem permanecer. Inspecione nomes,
labels e saída da execução antes de decidir qualquer remoção; nunca execute
prune. O teste conserva exit code diferente de zero em falha. Executá-lo exige
acesso ao socket rootless e ao bus systemd; um sandbox restrito pode bloquear o
preflight sem indicar defeito no host.

Resultados históricos: docs/LAB-0005-dev-python.md.
