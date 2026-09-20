# Conventions

Este documento define convenções de organização, nomenclatura e fluxo
utilizadas no repositório `kev-infra`.

Convenções descrevem como fazemos as coisas de forma consistente.

Elas não substituem ADRs.

Quando uma convenção envolver uma decisão arquitetural relevante,
a motivação deve ser registrada em um ADR correspondente.

---

## Princípio geral

A estrutura deve favorecer:

- clareza;
- isolamento;
- reprodutibilidade;
- revisão;
- manutenção;
- menor privilégio possível;
- menor duplicação possível de informação.

---

## Documentação

Os documentos possuem responsabilidades distintas.

### ARCHITECTURE

Formato:

    ARCHITECTURE.md

Responsabilidade:

    descrever a arquitetura atual e suas relações

É um documento vivo.

---

### BASELINE

Formato:

    BASELINE-N.md

Responsabilidade:

    registrar uma fotografia observada do sistema em determinado momento

Baselines são registros históricos.

Não devem ser modificados apenas para acompanhar mudanças futuras.

---

### ADR

Formato:

    ADR-NNNN-<descricao>.md

Exemplo:

    ADR-0001-docker-rootless.md

Responsabilidade:

    registrar uma decisão arquitetural,
    seu contexto, alternativas e consequências

ADRs são registros históricos.

Uma mudança de decisão deve preferencialmente gerar um novo ADR,
em vez de apagar a decisão anterior.

---

### LAB

Formato:

    LAB-NNNN-<descricao>.md

Exemplo:

    LAB-0001-docker-network-volume.md

Responsabilidade:

    registrar hipótese, procedimento, observações e resultados
    de um experimento técnico

Labs são registros históricos.

---

### RUNBOOK

Formato planejado:

    RUNBOOK-<descricao>.md

Responsabilidade:

    documentar procedimentos operacionais repetíveis

Exemplos:

    recuperação do Docker;
    restauração de backup;
    diagnóstico de um serviço.

---

### POLICY

Formato planejado:

    POLICY-<descricao>.md

Responsabilidade:

    registrar regras que devem ser obedecidas

Exemplos:

    tratamento de secrets;
    uso de privilégios;
    exposição de portas.

---

## Mapas locais

Um diretório deve possuir seu próprio `README.md` quando tiver
estrutura ou comportamento que não fique claro apenas observando
seus arquivos.

Exemplo:

    docs/ARCHITECTURE.md
        → mapa geral da infraestrutura

    docker/README.md
        → mapa específico da camada Docker

Não deve ser criado um `README.md` em cada diretório apenas por
uniformidade.

Documentação local deve existir quando agregar contexto real.

---

## Evitar duplicação

Um fato deve possuir, sempre que possível, uma fonte principal.

Exemplo:

    ARCHITECTURE.md
        → Docker rootless é parte da arquitetura

    ADR-0001
        → por que Docker rootless foi escolhido

    BASELINE
        → estado observado em determinado momento

    inventário gerado futuramente
        → versão e estado atual das ferramentas

Versões, estados temporários e outros fatos observáveis não devem
ser copiados desnecessariamente em vários documentos.

---

## Docker

A infraestrutura Docker versionada pertence a:

    docker/

Laboratórios pertencem a:

    docker/labs/

Cada laboratório deve possuir seu próprio diretório.

Exemplo:

    docker/labs/network-basic/
    docker/labs/volume-basic/

---

## Responsabilidade dos mecanismos Docker

Usar cada mecanismo para sua responsabilidade principal:

    imagem / container
        → executáveis, processos e ferramentas

    bind mount / volume
        → arquivos e dados

    rede
        → comunicação

    secret
        → credenciais e material sensível

Não utilizar uma rede como substituto para compartilhamento de
executáveis ou bibliotecas.

---

## Containers

Containers devem ser tratados como descartáveis.

Estado persistente não deve depender do filesystem gravável de um
container.

Dados que precisam sobreviver devem utilizar armazenamento
explicitamente definido.

---

## Redes

Isolamento é o comportamento padrão.

Conectividade adicional deve ser explícita.

Um container só deve participar de redes necessárias à sua função.

A nomenclatura e a estratégia definitiva das redes compartilhadas
serão definidas em ADR específico.

---

## Portas

Serviços de desenvolvimento que não precisam ser acessíveis pela
rede local devem preferir bind no loopback do host.

Exemplo:

    127.0.0.1:8080:8080

em vez de:

    8080:8080

Exceções devem ser deliberadas.

---

## Secrets

Secrets não devem ser versionados no Git.

Exemplos:

- senhas;
- tokens;
- chaves privadas;
- credenciais;
- arquivos `.env` contendo valores reais.

Arquivos de exemplo não devem conter credenciais reais.

---

## Git

Antes de um commit relevante:

    git status
    git diff --cached
    git diff --cached --check

Após o commit assinado:

    git verify-commit HEAD

Antes de enviar alterações:

    git log --oneline --decorate -4

Esses comandos não substituem testes específicos da alteração.

---

## Commits

Preferir commits pequenos e com responsabilidade clara.

O formato atualmente utilizado é:

    <tipo>(<escopo>): <resumo>

O escopo pode ser omitido quando não agregar informação.

Exemplos:

    chore(infra): establish host baseline
    docs(adr): adopt rootless Docker
    test(docker): add network and volume labs

O commit deve representar uma unidade lógica de alteração.

Evitar misturar em um mesmo commit mudanças independentes.

---

## Mudanças arquiteturais

Quando uma alteração modificar estrutura ou comportamento relevante,
verificar se também exige atualização de:

    ARCHITECTURE.md

e, dependendo do caso:

    ADR
    LAB
    RUNBOOK
    POLICY
    README local

A documentação deve fazer parte da própria alteração quando possível.

---

## Estado gerado

Futuramente, fatos observáveis da máquina poderão ser coletados
automaticamente por scripts.

Exemplo planejado:

    docs/generated/CURRENT-STATE.md

O estado gerado não substituirá a documentação arquitetural.

A separação será:

    documentação curada
        → intenção e arquitetura

    documentação gerada
        → estado observado

    documentação histórica
        → decisões, experimentos e snapshots

---

## Estado de uma arquitetura ou componente

Ao documentar infraestrutura, distinguir quando necessário entre:

    conceitual
        ideia ou modelo em discussão

    planejado
        intenção aceita, mas ainda não implementada

    experimental
        implementação criada para validação

    adotado
        parte da arquitetura vigente

    depreciado
        ainda pode existir, mas não deve ser usado em novas implementações

    removido
        não faz mais parte da arquitetura

Essa distinção evita que diagramas de planejamento sejam confundidos
com o estado real da máquina.
