# ADR-0002: Estratégia de redes Docker

## Status

Accepted

## Contexto

O ambiente utiliza Docker Engine em modo rootless e pretende hospedar
múltiplos projetos, ambientes de desenvolvimento e serviços
compartilhados.

Os experimentos do LAB-0001 validaram:

- comunicação entre containers da mesma rede;
- resolução DNS interna;
- isolamento entre redes diferentes;
- conexão dinâmica de um container a múltiplas redes;
- restauração do isolamento após desconexão.

Precisamos definir como projetos, ferramentas e serviços
compartilhados devem se comunicar sem criar uma rede única onde todos
os containers tenham acesso entre si.

Uma única rede global simplificaria a conectividade, mas aumentaria o
acoplamento entre projetos e ampliaria o blast radius de falhas ou
comprometimentos.

Também foi considerado o uso de uma rede de ferramentas, contendo
ambientes como Python, C e desenvolvimento embarcado.

Entretanto, uma rede fornece comunicação entre processos. Ela não
compartilha executáveis, bibliotecas ou toolchains entre containers.

---

## Decisão

A arquitetura Docker utilizará segmentação de redes.

Não haverá uma única rede global à qual todos os containers sejam
conectados automaticamente.

A estratégia será composta por:

1. redes internas por projeto;
2. redes compartilhadas por finalidade;
3. containers conectados a múltiplas redes somente quando necessário;
4. conectividade explícita por padrão;
5. containers de ferramentas conectados às redes dos projetos que
   precisarem acessar.

---

## Redes internas por projeto

Cada projeto deve possuir uma ou mais redes próprias quando houver
necessidade de comunicação interna.

Exemplo conceitual:

    brsa_internal
    ├── api
    ├── postgres
    └── redis

    metra_internal
    ├── api
    ├── simulator
    └── acquisition

Serviços internos não devem ser expostos a redes compartilhadas sem
necessidade.

Bancos de dados, caches e componentes de backend devem permanecer
isolados sempre que possível.

---

## Redes compartilhadas por finalidade

Serviços utilizados por múltiplos projetos podem possuir redes
compartilhadas específicas.

Exemplos conceituais:

    proxy_net

    monitoring_net

    forge_net

Esses nomes representam finalidade, não uma implementação obrigatória.

Uma rede compartilhada só deve ser criada quando existir um serviço
real que justifique sua existência.

Não será criada uma rede `infra_shared` genérica apenas para fornecer
conectividade universal.

---

## Ciclo de vida de redes compartilhadas

Quando uma rede for utilizada por múltiplos projetos independentes,
seu ciclo de vida não deve pertencer a apenas um deles.

Nesses casos, a rede poderá ser criada externamente ao projeto
Compose e referenciada como:

    external: true

Assim:

    Projeto A
        │
        ├──── rede compartilhada
        │
    Projeto B

a remoção do Projeto A não destrói a rede utilizada pelo Projeto B.

Esse comportamento deverá ser validado experimentalmente antes da
primeira adoção permanente.

---

## Containers em múltiplas redes

Um container pode participar de mais de uma rede quando sua função
exigir.

Exemplo:

                         proxy_net
                             │
                      brsa-frontend
                             │
                       brsa_internal
                             │
                         brsa-api
                             │
                         postgres

Nesse exemplo:

- o frontend possui acesso à rede utilizada pelo proxy;
- o frontend também pode acessar componentes necessários do projeto;
- o PostgreSQL permanece somente na rede interna.

A associação a múltiplas redes deve ser explícita.

---

## Containers de ferramentas

Ambientes como:

- Python;
- Node.js;
- C/C++;
- toolchains embarcadas;
- ferramentas de teste;

são tratados como ambientes de execução, não como serviços fornecidos
por uma rede de ferramentas.

Exemplo:

    código do projeto
          │
          │ bind mount
          ▼
       dev-python
          │
          └── metra_internal

O código é disponibilizado ao container por bind mount ou volume.

A rede permite que o container de ferramentas converse com serviços
do projeto quando necessário.

Outro ambiente pode montar o mesmo código:

    código do projeto
       ├── dev-python
       ├── dev-c
       └── dev-embedded

Não é necessária uma `tools_net` apenas para compartilhar Python,
compiladores ou bibliotecas.

Uma rede específica de ferramentas só faria sentido caso existissem
serviços de rede reais associados a essas ferramentas.

---

## Publicação de portas

Serviços que precisam ser acessados somente pelo próprio host devem
preferir bind no loopback.

Exemplo:

    127.0.0.1:8080:8080

em vez de:

    8080:8080

A exposição à rede local deve ser deliberada.

---

## Regras

Por padrão:

- projetos são isolados;
- conectividade adicional é explícita;
- serviços internos permanecem internos;
- bancos de dados não entram em redes compartilhadas sem necessidade;
- uma rede compartilhada deve possuir uma finalidade identificável;
- containers só devem participar das redes necessárias à sua função;
- ferramentas são fornecidas por imagens/containers, não por redes;
- bind mounts e volumes fornecem arquivos e dados;
- redes fornecem comunicação.

---

## Alternativas consideradas

### Uma única rede global

Exemplo:

    infra_shared
    ├── BRSA
    ├── Metra Nexus
    ├── Forgejo
    ├── bancos
    ├── ferramentas
    └── monitoramento

Vantagem:

- configuração simples.

Desvantagens:

- baixo isolamento;
- maior acoplamento;
- maior superfície de comunicação;
- maior blast radius;
- dificuldade crescente de compreender quem pode acessar quem.

Não adotada.

### Rede global de ferramentas

Exemplo:

    tools_net
    ├── Python
    ├── C
    └── Embedded

Não adotada como mecanismo para compartilhar toolchains, pois a rede
não fornece executáveis ou bibliotecas aos demais containers.

Containers de ferramentas podem ser reutilizados sem pertencer a uma
rede global.

---

## Consequências

### Positivas

- maior isolamento entre projetos;
- menor blast radius;
- topologia mais explícita;
- possibilidade de controlar comunicação por finalidade;
- serviços internos ficam menos expostos;
- projetos mantêm ciclos de vida independentes.

### Negativas

- mais redes para compreender e administrar;
- alguns containers precisarão participar de múltiplas redes;
- configurações Compose poderão ser mais detalhadas;
- serviços compartilhados exigirão planejamento de ciclo de vida.

Esses custos são considerados aceitáveis em troca de maior isolamento
e clareza arquitetural.

---

## Validação necessária

Antes de adotar a primeira rede compartilhada permanente, deve ser
executado um laboratório que valide:

    Compose A
        │
        └──── shared_test_net ────┐
                                  │
    Compose B ────────────────────┘

O laboratório deverá provar que:

- dois projetos Compose independentes podem utilizar a mesma rede
  externa;
- ambos conseguem se comunicar quando conectados à rede;
- destruir um projeto não destrói a rede compartilhada;
- o outro projeto continua funcionando;
- a rede pode ser removida deliberadamente somente após deixar de ser
  utilizada.

Esse experimento será registrado como LAB-0002.

---

## Validação concluída

A validação prevista neste ADR foi executada no:

    LAB-0002: Rede externa compartilhada entre projetos Compose

Resultado:

    PASS

O experimento confirmou que:

- dois projetos Compose independentes podem utilizar a mesma rede externa;
- os serviços podem se comunicar por DNS e HTTP nessa rede;
- a remoção de um projeto não remove a rede externa;
- o outro projeto continua funcionando;
- serviços removidos deixam de ser resolvidos pelo DNS da rede;
- uma rede com endpoints ativos não pode ser removida;
- após a remoção dos projetos, a rede externa continua existindo;
- sem endpoints ativos, a rede pode ser removida explicitamente.

A validação confirma o mecanismo técnico previsto por esta decisão.

Ela não implica a criação de uma rede global nem elimina a exigência
de que redes compartilhadas tenham finalidade explícita.
