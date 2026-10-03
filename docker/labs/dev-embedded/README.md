# Laboratório dev-embedded

Na raiz da worktree:

```bash
./scripts/check-dev-embedded --config-only
./scripts/check-dev-embedded --build  # exige autorização de Docker/rede
./scripts/check-dev-embedded          # imagem local, sem pull/build
```

Runner: Python 3 stdlib do control plane e Docker CLI; nenhuma dependência
nova no host. Config-only usa Compose JSON sem daemon. As demais execuções
fazem preflight check-infra e exigem host 1000:1000.

Valida configuração e inspeção real de cada container; EDIT/TEST/SANDBOX,
rootfs, caps, network none, mounts, ownership e limites. Usa fixture copiado
para scratch exclusivo, nunca o projeto real do operador. EDIT produz objetos,
ELF/BIN/HEX/MAP, readelf/nm/disassembly; verifica arquitetura, entrypoint,
vetores, seções, segmentos, tamanho e roundtrip HEX → BIN. Host edita fonte,
remove artefato e recompila num container novo. TEST rejeita escrita e compila
em /tmp sem mudar o projeto; SANDBOX recebe somente texto do fixture por comando,
compila em tmpfs e perde tudo após recriação. Sem execução de firmware.

Dois builds limpos em containers independentes, no mesmo caminho, imprimem
SHA-256 de objetos/ELF/BIN/HEX/MAP. Um build TEST compara saída em outro caminho,
imprime hashes, igualdade e diffs DWARF/MAP. Igualdade é medida, não um requisito
artificial de aprovação. Divergências novas exigem investigação antes de
classificar reprodutibilidade; não alterar flags ou retirar debug para igualar.
Não mede builds em outro diretório de fonte, host ou versão de toolchain.

Execução completa cria seis containers sequenciais com token phase7b exclusivo.
Cleanup confere label Compose e remove por ID somente seus containers; verifica
que nenhum container com seu label permaneceu. Remove apenas scratch próprio.
Não cria redes/volumes; não usa prune nem remove imagens. SIGKILL pode deixar
recursos: inspecionar label/identidade antes de qualquer remoção manual.
Imagem, camadas e cache permanecem deliberadamente.

Bloqueios de socket/buses no sandbox do agente precisam de aprovação pontual;
não são evidência de defeito do host. Limites: sem OOM/saturação de PIDs,
firmware real, periféricos, interrupts completos, hardware ou emulador.
[Resultados observados](../../../docs/LAB-0007-dev-embedded.md).
