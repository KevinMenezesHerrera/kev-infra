# LAB-0001 — Redes e persistência Docker

## Objetivo

Validar propriedades básicas do ambiente Docker rootless:

- criação de redes isoladas;
- resolução DNS entre serviços;
- comunicação entre containers da mesma rede;
- isolamento entre redes diferentes;
- conexão e desconexão dinâmica de um container;
- persistência de dados usando volumes nomeados.

## Ambiente

- Docker Engine rootless
- Docker Compose
- imagem usada nos testes: `busybox:1.37.0`

---

## Teste 1 — Comunicação dentro da mesma rede

Topologia:

    network-basic_lab_a
    ├── service-a
    └── client-a

    network-basic_lab_b
    └── outsider

`service-a` executou um servidor HTTP na porta 8080.

Teste:

    client-a -> http://service-a:8080

Resultado:

    hello from service-a

Status: PASS

Validado:

- DNS interno do Docker;
- comunicação entre containers da mesma rede.

---

## Teste 2 — Isolamento entre redes

Teste:

    outsider -> http://service-a:8080

Resultado inicial:

    wget: bad address 'service-a:8080'

Status: PASS

A falha da conexão era o comportamento esperado.

O container `outsider`, conectado apenas à `network-basic_lab_b`,
não conseguia resolver o serviço existente em `network-basic_lab_a`.

---

## Teste 3 — Conexão dinâmica entre redes

O container `outsider` foi conectado temporariamente também à rede:

    network-basic_lab_a

Depois disso passou a alcançar:

    http://service-a:8080

Resultado:

    hello from service-a

Status: PASS

Após executar `docker network disconnect`, o isolamento foi restaurado.

Isso valida o modelo de containers de ferramentas que podem ser
conectados temporariamente à rede de um projeto.

---

## Teste 4 — Persistência com volume

Topologia:

    container stateful
           |
           | /data
           v
    volume-basic_lab_data

Foi escrito no volume:

    persistent-data-test

O container foi destruído com:

    docker compose down

O volume permaneceu.

Um novo container foi criado com:

    docker compose up -d

O novo container conseguiu ler novamente o dado persistido.

Status: PASS

Validado:

- container é descartável;
- volume possui ciclo de vida independente do container.

---

## Limpeza

Após os testes:

- todos os containers foram removidos;
- todas as redes criadas pelos laboratórios foram removidas;
- todos os volumes dos laboratórios foram removidos;
- permaneceram somente as redes padrão do Docker;
- imagens `busybox` e `hello-world` permaneceram em cache.

## Resultado final

| Propriedade | Resultado |
|---|---|
| Docker rootless | PASS |
| DNS entre containers da mesma rede | PASS |
| Comunicação HTTP dentro da rede | PASS |
| Isolamento entre redes | PASS |
| Conexão dinâmica a outra rede | PASS |
| Desconexão restaura isolamento | PASS |
| Persistência por volume | PASS |
| Remoção/recriação de container sem perda do volume | PASS |
