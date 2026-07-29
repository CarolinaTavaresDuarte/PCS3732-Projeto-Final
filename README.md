# Snake Pi

**Snake Pi** é uma implementação do clássico jogo Snake desenvolvida para a disciplina **Laboratório de Processadores** da Escola Politécnica da Universidade de São Paulo (USP).

O projeto foi desenvolvido para a plataforma **Raspberry Pi 4** utilizando a **Freenove Projects Board v1.2**, integrando diversos periféricos físicos a uma aplicação gráfica executada no monitor HDMI.

A arquitetura foi projetada para manter a lógica do jogo independente do hardware, permitindo executar o projeto tanto na Raspberry Pi quanto em modo de simulação em qualquer computador com Python.

---

# Funcionalidades

- Menu inicial com navegação por botões físicos
- Sistema de níveis
- Três níveis de dificuldade (Easy, Normal e Hard)
- Frutas normais e especiais
- Obstáculos conforme a dificuldade
- Ajuste da velocidade por potenciômetro
- Ranking persistente em arquivo JSON
- Exibição gráfica utilizando Pygame
- Integração com os periféricos da Freenove Projects Board
- Execução em modo simulado (sem hardware)
- Testes automatizados da lógica do jogo

---

# Hardware utilizado

- Raspberry Pi 4 Model B
- Freenove Projects Board v1.2
- LCD1602
- Display de 4 dígitos
- Matriz LED 8×8
- LED Bar Graph
- Buzzers ativo e passivo
- Potenciômetro
- Botões físicos
- Leitor RFID (opcional)

---

# Estrutura do projeto

```text
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
│
├── tests/
│
├── docs/
│
├── README.md
├── LICENSE
├── requirements.txt
├── install.sh
└── conftest.py
```

---

# Organização do software

O projeto foi dividido em módulos independentes.

| Módulo | Responsabilidade |
|---------|------------------|
| `game/` | Lógica do jogo |
| `hardware/` | Drivers dos periféricos |
| `display/` | Renderização gráfica (Pygame) |
| `threads/` | Atualização assíncrona dos periféricos |
| `utils/` | Utilitários compartilhados |
| `config.py` | Configuração centralizada do projeto |
| `main.py` | Inicialização e execução da aplicação |

Essa organização reduz o acoplamento entre os componentes e facilita manutenção, testes e reutilização do código.

---

# Requisitos

- Raspberry Pi OS Bookworm
- Python 3.11
- Raspberry Pi 4
- Freenove Projects Board v1.2

Também é possível executar o projeto em modo de simulação, sem qualquer hardware conectado.

---

# Instalação

Clone o repositório:

```bash
git clone <repositorio>
cd projeto
```

Conceda permissão ao instalador:

```bash
chmod +x install.sh
```

Execute:

```bash
./install.sh
```

O script instala automaticamente as dependências necessárias para o projeto.

---

# Execução

Na Raspberry Pi:

```bash
cd src
python3 main.py
```

Modo simulado (sem hardware):

```bash
cd src
python3 main.py --sim
```

Executar em janela:

```bash
python3 main.py --windowed
```

Log detalhado:

```bash
python3 main.py --log DEBUG
```

---

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

---

# Periféricos utilizados

| Periférico | Função |
|------------|--------|
| LCD1602 | Exibe informações da partida |
| Display de 4 dígitos | Pontuação |
| Matriz 8×8 | Animações de eventos |
| LED Bar Graph | Velocidade da cobra |
| Buzzers | Efeitos sonoros |
| Potenciômetro | Controle de velocidade |
| Botões | Movimento e navegação |
| RFID | Seleção opcional de dificuldade |

---

# Testes

A lógica do jogo foi desenvolvida independentemente do hardware, permitindo a execução de testes automatizados.

Foram implementados **34 testes**, cobrindo:

- movimentação da cobra;
- colisões;
- frutas;
- obstáculos;
- sistema de níveis;
- dificuldades;
- persistência do ranking;
- menus;
- displays;
- estado compartilhado.

Executar:

```bash
python3 tests/test_game_logic.py -v
```

ou

```bash
python3 -m pytest tests -v
```

---

# Documentação

A documentação completa do projeto encontra-se na pasta `docs/`, incluindo:

- relatório técnico;
- diagramas da arquitetura;
- modelagem do sistema;
- documentação de hardware;
- resultados experimentais.

---

# Licença

Este projeto é distribuído sob os termos da **MIT License**.

Copyright © 2026 CarolinaTavaresDuarte.

Consulte o arquivo [`LICENSE`](LICENSE) para o texto completo da licença.

Este projeto é distribuído sob os termos da licença **GNU GPL v3**.

Consulte o arquivo `LICENSE` para mais informações.
