# LAB-0002: Rede externa compartilhada entre projetos Compose

## Objetivo

Validar o uso de uma rede Docker externa por dois projetos Compose
independentes.

O laboratório verifica se:

- uma rede declarada como `external: true` precisa existir previamente;
- dois projetos Compose independentes podem utilizar a mesma rede;
- serviços dos dois projetos conseguem se comunicar por DNS e HTTP;
- destruir um projeto não destrói a rede compartilhada;
- o outro projeto continua funcionando;
- serviços removidos deixam de ser resolvidos pelo DNS da rede;
- uma rede em uso não pode ser removida;
- a rede permanece após a remoção dos projetos;
- a rede pode ser removida explicitamente quando deixa de possuir
  endpoints ativos.

---

## Topologia

Foram utilizados dois projetos Compose independentes:

    Project A                         Project B

    service-a                        service-b
    BusyBox httpd                    BusyBox httpd
       :8080                            :8080
        │                                │
        └──────── lab_shared_net ────────┘

A rede `lab_shared_net` foi criada fora dos dois projetos Compose.

Nos dois arquivos Compose ela foi declarada como:

    networks:
      shared:
        external: true
        name: lab_shared_net

---

## Estrutura

    docker/labs/shared-network/
    ├── project-a/
    │   └── compose.yaml
    └── project-b/
        └── compose.yaml

Os projetos possuem nomes Compose distintos:

    lab2-a
    lab2-b

---

## Teste 1 — Rede externa inexistente

Inicialmente:

    docker network ls --filter name=lab_shared_net

não encontrou a rede.

Foi executado:

    docker compose \
      -f docker/labs/shared-network/project-a/compose.yaml \
      up -d

Resultado:

    network lab_shared_net declared as external, but could not be found

### Resultado

PASS.

O Compose não criou automaticamente uma rede declarada como externa.

Isso confirma que seu ciclo de vida não pertence ao projeto Compose.

---

## Teste 2 — Criação externa da rede

A rede foi criada explicitamente:

    docker network create lab_shared_net

A inspeção mostrou:

    Driver: bridge
    Scope: local
    IPv4: enabled
    IPv6: disabled

Subnet observada durante o laboratório:

    172.18.0.0/16

Gateway observado:

    172.18.0.1

### Resultado

PASS.

---

## Teste 3 — Dois projetos independentes na mesma rede

Foram iniciados:

    lab2-a-service-a-1
    lab2-b-service-b-1

Ambos apareceram conectados a:

    lab_shared_net

### Resultado

PASS.

Dois projetos Compose com ciclos de vida independentes utilizaram a
mesma rede externa.

---

## Teste 4 — Comunicação de A para B

Dentro de `service-a` foi executado:

    wget -qO- http://service-b:8080

Resposta:

    hello from project-b

### Resultado

PASS.

O DNS interno da rede resolveu `service-b` e a comunicação HTTP foi
bem-sucedida.

---

## Teste 5 — Comunicação de B para A

Dentro de `service-b` foi executado:

    wget -qO- http://service-a:8080

Resposta:

    hello from project-a

### Resultado

PASS.

A comunicação entre os projetos foi bidirecional.

---

## Teste 6 — Remoção do projeto A

Foi executado:

    docker compose \
      -f docker/labs/shared-network/project-a/compose.yaml \
      down

O container:

    lab2-a-service-a-1

foi removido.

A rede:

    lab_shared_net

continuou existindo.

O container:

    lab2-b-service-b-1

continuou executando e conectado à rede.

Acesso local ao HTTP de `service-b` retornou:

    hello from project-b

### Resultado

PASS.

A destruição do projeto A não afetou o ciclo de vida da rede externa
nem do projeto B.

---

## Teste 7 — Remoção do serviço do DNS

Após a destruição do projeto A, foi executado no projeto B:

    wget -T 3 -qO- http://service-a:8080

Resultado:

    wget: bad address 'service-a:8080'

### Resultado

PASS.

O serviço removido deixou de ser resolvido pelo DNS da rede.

---

## Teste 8 — Tentativa de remover rede em uso

Enquanto `service-b` ainda estava conectado, foi executado:

    docker network rm lab_shared_net

Resultado:

    network lab_shared_net has active endpoints

O endpoint ativo identificado correspondia ao container do projeto B.

### Resultado

PASS.

O Docker recusou remover uma rede enquanto ainda existiam endpoints
ativos.

---

## Teste 9 — Remoção do projeto B

Foi executado:

    docker compose \
      -f docker/labs/shared-network/project-b/compose.yaml \
      down

Após isso não havia containers do laboratório em execução.

A rede:

    lab_shared_net

continuou existindo.

### Resultado

PASS.

A rede externa sobreviveu à remoção de todos os projetos que a
utilizavam.

---

## Teste 10 — Remoção explícita da rede

Sem endpoints ativos, foi executado:

    docker network rm lab_shared_net

Resultado:

    lab_shared_net

Uma nova consulta:

    docker network ls --filter name=lab_shared_net

não encontrou a rede.

### Resultado

PASS.

A rede pôde ser removida explicitamente quando deixou de estar em uso.

---

## Resultado geral

Todos os testes planejados passaram.

    Propriedade                                             Resultado
    ------------------------------------------------------------------
    Compose não cria rede external inexistente             PASS
    Dois projetos usam a mesma rede externa                PASS
    DNS entre projetos independentes                       PASS
    HTTP entre projetos independentes                      PASS
    Remover projeto A preserva a rede                      PASS
    Projeto B continua funcionando                         PASS
    Serviço removido desaparece do DNS                     PASS
    Rede com endpoint ativo não pode ser removida          PASS
    Rede sobrevive à remoção dos projetos                  PASS
    Rede sem endpoints pode ser removida explicitamente    PASS

---

## Conclusão

O laboratório confirmou o mecanismo previsto no ADR-0002.

Uma rede Docker externa pode possuir ciclo de vida independente dos
projetos Compose que a utilizam.

Esse modelo é adequado para futuras redes compartilhadas por
finalidade, quando múltiplos projetos ou serviços realmente precisarem
compartilhar a mesma rede.

O resultado não implica a criação de uma rede global.

Redes compartilhadas continuam devendo possuir finalidade explícita e
ser utilizadas somente pelos containers que realmente necessitam
delas.
