# LAB-0005 — Fundação Python: bind, persistência, modos e recursos

Executado em 2026-09-24 no ambiente descrito no LAB-0004. Resultado final: PASS.

## Reprodução

```bash
./scripts/check-dev-python
./scripts/tests/check-infra-test
```

Procedimentos e limites: docker/labs/dev-python/README.md. O script integrado
executa também o experimento UID/GID. Não usa dados reais. A primeira execução
parou antes do build porque o verificador esperava mem_limit numérico, mas
Compose fornece string no JSON. A conversão foi corrigida e as duas execuções
subsequentes passaram; nenhuma restrição do container foi relaxada.

## Resultados observados

| Teste | Resultado |
| --- | --- |
| check-infra | 0 FAIL; WARN informativo enquanto havia alterações Git |
| Mapeamento UID/GID | 0:0 → 1000:1000; 1000:1000 → 100999:100999 |
| Compose | JSON válido; cinco configurações verificadas sem mounts proibidos/privileged |
| Build | Python 3.13.7, imagem oficial slim-bookworm fixada por digest |
| Bind host → container | Conteúdo `from host` lido corretamente |
| Bind container → host | Conteúdo `from container` lido e alterado pelo host |
| Remoção pelo host | Arquivo criado pelo container removido normalmente |
| Subdiretórios | Criados pelo container, UID/GID 1000:1000 no host |
| Recriação EDIT | Conteúdo editado e subdiretório preservados após remoção |
| TEST | Leitura funciona; escrita retorna errno 30, EROFS |
| SANDBOX | Sem binds/volumes persistentes, projeto ou sockets; rootfs recusa escrita |
| Proteções | CapEff=0, NoNewPrivs=1; mounts efetivos inspecionados |
| tmpfs | Escrita funciona; arquivos ausentes após recriação |
| Memória | memory.max=268435456; alocação controlada de 8 MiB bem-sucedida |
| CPU | cpu.max=50000 100000; 15 períodos de throttling em 1,5 s |
| Volume | Dado preservado após remoção do primeiro container |
| Camada gravável | Arquivo ausente em novo container da mesma imagem |
| Regressão check-infra | Todos os 10 testes existentes passaram |

Na última execução, memory.current=18599936 bytes após alocar 8 MiB.
os.cpu_count() retornou 16: quota não equivale a afinidade nem ao número de CPUs
visíveis. O Docker informa ausência de suporte a cpuset e a limites de I/O
(io.weight e io.max); memória e CPU por quota funcionaram em cgroup v2/systemd.
Não foi provocado OOM nem pressão severa; a medição de memória comprova o valor
do cgroup e uma alocação pequena, não exercita o comportamento no limite.

## Recursos e limpeza

Imagem baixada: python:3.13.7-slim-bookworm, digest
`sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d`.
Imagem construída: kev-infra/dev-python:3.13.7 (duas construções).
BusyBox 1.37.0 preexistente foi reutilizado.

Execuções completas: `phase6-9254d2eb0a24` e `phase6-c232f6310d5c`.
Cada uma criou cinco containers Compose (EDIT duas vezes, TEST uma, SANDBOX
duas) e dois containers de armazenamento, todos removidos. O experimento
UID/GID criou dois containers em cada uma de suas duas execuções: total de
18 containers descartáveis nesta tarefa. Nenhuma rede criada.

Volumes criados e removidos separadamente, após conferir seus labels:

- phase6-9254d2eb0a24-data
- phase6-c232f6310d5c-data

Diretórios scratch de cada experimento foram removidos. Não havia volumes ou
containers preexistentes. Imagens e cache de build permanecem deliberadamente;
não foi executado prune. As três redes padrão e as duas imagens iniciais foram
preservadas.

## Limitações

Python 3.13.7 é um pin reproduzível, não indicação de versão mais recente;
atualização de segurança requer revisão. A base não contém dependências de
aplicação, pytest ou compiladores. tmpfs/venv e caches são temporários e pequenos.
Downloads em runtime não funcionam com network_mode none. Uso com serviços ou
dependências maiores exige extensão deliberada por projeto. TEST protege o
bind contra escrita pelo container, mas não congela alterações simultâneas do
host. SANDBOX não constitui autorização genérica para código hostil.
