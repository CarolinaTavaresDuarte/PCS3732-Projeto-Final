# Snake Pi

**Snake Pi** é uma implementação do clássico jogo Snake desenvolvida
para a disciplina **Laboratório de Processadores** da Escola Politécnica
da Universidade de São Paulo (USP).

O projeto foi desenvolvido para a plataforma **Raspberry Pi 4**
utilizando a **Freenove Projects Board v1.2**, integrando periféricos
físicos a uma aplicação gráfica executada em monitor HDMI.

A arquitetura foi projetada para manter a lógica do jogo independente do
hardware, permitindo executar o projeto tanto na Raspberry Pi quanto em
modo de simulação em qualquer computador com Python.

------------------------------------------------------------------------

# Funcionalidades

-   Menu inicial
-   Sistema de níveis
-   Três dificuldades
-   Frutas normais e especiais
-   Obstáculos
-   Ajuste de velocidade por potenciômetro
-   Ranking persistente
-   Interface gráfica em Pygame
-   Display de quatro dígitos (74HC595)
-   LCD1602
-   Buzzers
-   Execução em modo simulado
-   34 testes automatizados

------------------------------------------------------------------------

# Hardware utilizado

-   Raspberry Pi 4 Model B
-   Freenove Projects Board v1.2
-   LCD1602
-   Display de quatro dígitos e sete segmentos
-   74HC595
-   ADS7830
-   Potenciômetro
-   Botões físicos
-   Botão do joystick
-   Buzzers ativo e passivo
-   Leitor RFID (opcional)
-   Monitor HDMI

------------------------------------------------------------------------

# Estrutura do projeto

``` text
projeto/
├── src/
│   ├── display/
│   ├── game/
│   ├── hardware/
│   ├── threads/
│   ├── utils/
│   ├── config.py
│   ├── diagnostico_placa.py
│   ├── calibrar_joystick.py
│   └── main.py
├── tests/
├── docs/
│   └── diagramas/
├── README.md
├── LICENSE
├── requirements.txt
├── install.sh
└── conftest.py
```

------------------------------------------------------------------------

# Organização do software

  Módulo        Responsabilidade
  ------------- ----------------------------
  `game/`       Lógica do jogo
  `hardware/`   Drivers dos periféricos
  `display/`    Interface gráfica (Pygame)
  `threads/`    Atualização assíncrona
  `utils/`      Utilitários
  `config.py`   Configuração centralizada
  `main.py`     Inicialização

------------------------------------------------------------------------

# Requisitos

-   Raspberry Pi OS Bookworm
-   Python 3.11
-   Raspberry Pi 4
-   Freenove Projects Board v1.2

Também é possível executar em modo simulado.

------------------------------------------------------------------------

# Instalação

``` bash
git clone https://github.com/CarolinaTavaresDuarte/PCS3732-Projeto-Final.git
cd PCS3732-Projeto-Final
chmod +x install.sh
./install.sh
```

------------------------------------------------------------------------

# Execução

Raspberry Pi:

``` bash
cd src
python3 main.py
```

Modo simulado:

``` bash
python3 main.py --sim
```

Janela:

``` bash
python3 main.py --windowed
```

Logs:

``` bash
python3 main.py --log DEBUG
```

------------------------------------------------------------------------

# Controles

## Durante a partida

| Controle | Função |
|----------|--------|
| Botão Azul | Cima |
| Botão Vermelho | Baixo |
| Botão Amarelo | Esquerda |
| Botão Verde | Direita |
| Clique do joystick | Pausar / Continuar |
| Potenciômetro | Ajuste da velocidade |

## Menus

| Controle | Função |
|----------|--------|
| Botões Azul/Vermelho | Navegação |
| Clique do joystick | Confirmar |

Como alternativa, também é possível utilizar o teclado durante a execução em um computador.

------------------------------------------------------------------------

# Testes

Foram implementados **34 testes automatizados**, cobrindo:

-   lógica do jogo;
-   menus;
-   ranking;
-   display;
-   obstáculos;
-   dificuldades;
-   estado compartilhado.

Executar:

``` bash
python3 tests/test_game_logic.py -v
```

ou

``` bash
python3 -m pytest tests -v
```

------------------------------------------------------------------------

# Desenvolvimento

O projeto foi desenvolvido de forma incremental utilizando:

-   commits incrementais;
-   branches;
-   Pull Requests;
-   quatro Releases;
-   avaliação por pares via GitHub Issues.

------------------------------------------------------------------------

# Documentação

A pasta `docs/` contém:

-   relatório final (SBC);
-   diagramas em D2, SVG e PDF;
-   documentação técnica;
-   resultados experimentais.

Os diagramas utilizados no GitHub encontram-se em:

``` text
docs/diagramas/
```

------------------------------------------------------------------------

# Releases

-   v1.0
-   v2.0
-   v3.0
-   v4.0

------------------------------------------------------------------------

# Licença

Este projeto é distribuído sob a **MIT License**.

Consulte o arquivo `LICENSE`.
