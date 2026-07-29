# Snake Pi

Jogo Snake para **Raspberry Pi 4 + Freenove Projects Board v1.2**, renderizado
em monitor HDMI via Pygame, com os periféricos físicos da placa espelhando o
estado da partida em tempo real.

Projeto da disciplina **Laboratório de Processadores** — Escola Politécnica da USP.

---

## Organização do repositório

```
projeto/
├── src/                     # código-fonte (Python)
│   ├── main.py              # ponto de entrada e loop principal
│   ├── config.py            # pinagem e parâmetros (fonte única de verdade)
│   ├── diagnostico_placa.py # script de diagnóstico do hardware
│   ├── game/                # lógica pura do jogo (sem hardware)
│   ├── display/             # renderização Pygame
│   ├── hardware/            # drivers dos periféricos
│   ├── threads/             # threads periféricas
│   └── utils/               # log e compatibilidade I²C
├── tests/                   # testes automatizados (31 casos)
├── docs/
│   ├── relatorio.md         # relatório do projeto
│   ├── diagramas/           # fontes editáveis em D2
│   └── figuras/             # diagramas renderizados (SVG) e fotos
├── README.md
├── LICENSE                  # GNU GPLv3
├── requirements.txt
├── install.sh               # instalação automatizada na Pi
└── SEM_SUDO.md              # roteiro alternativo sem privilégios de root
```

---

## Descrição

O jogo roda inteiramente na Raspberry Pi. A cobra aparece no monitor HDMI,
controlada pelo joystick analógico ou pelos botões coloridos da placa, enquanto
os periféricos participam da experiência:

- **LCD1602** — score e nível; mensagem de Game Over
- **Display de 4 dígitos** — score
- **Matriz 8×8** — animações de evento (fruta, level up, recorde, Game Over)
- **Bar graph** — velocidade atual
- **Buzzers** — retorno sonoro (bipe da fruta, melodias de level up, recorde,
  Game Over)
- **RFID** — seleção de dificuldade por cartão
- **Botões** — direcional (D-pad)
- **Potenciômetro** — ajuste de velocidade em tempo real

### Funcionalidades

- Menu navegável (Start Game, High Score, Configurações, Sair)
- Crescimento, frutas aleatórias, colisão com parede e consigo mesma
- Game Over e reinício; sistema de níveis
- Frutas especiais temporárias (com contador na tela)
- Obstáculos por dificuldade; ranking persistido em JSON
- Três dificuldades: Easy (parede não mata), Normal, Hard

---

## Instalação

### 1. Habilitar I²C e SPI

```bash
sudo raspi-config
# Interface Options > I2C > Yes
# Interface Options > SPI > Yes
# reiniciar
```

Se o SPI for usado com o RFID, adicione ao `config.txt` para liberar o GPIO 7
(botão do joystick), que conflita com o CE1 do SPI:

```
dtoverlay=spi0-1cs
```

### 2. Dependências

```bash
cd projeto
chmod +x install.sh
./install.sh
```

Sem privilégios de root, ver **SEM_SUDO.md**.

---

## Como executar

No terminal **da própria Raspberry Pi** (por SSH o Pygame não abre):

```bash
cd projeto/src
python3 main.py
```

Opções:

```bash
python3 main.py --sim         # sem hardware (testar no PC)
python3 main.py --windowed    # em janela
python3 main.py --log DEBUG   # log detalhado
```

### Antes de jogar com hardware

```bash
cd projeto/src
python3 diagnostico_placa.py   # descobre a topologia do 74HC595
```

Ajuste `BUS_TOPOLOGY` em `src/config.py` conforme o resultado (teste 5).

---

## Controles

### Botões coloridos (direcional)

| Botão | GPIO | Direção |
|---|---|---|
| Azul | 20 | Cima |
| Vermelho | 21 | Baixo |
| Amarelo | 26 | Esquerda |
| Verde | 16 | Direita |

O **joystick é apenas um botão de confirmar** (GPIO 7): o clique confirma nos
menus, pausa na partida e reinicia no Game Over. **O manche não move a cobra** —
o movimento é só pelos botões coloridos (ou teclado). Isso também remove a
dependência do I²C para o joystick.

> **GPIO 7 e o SPI:** o botão do joystick fica no GPIO 7, que é o CE1 do SPI0.
> Se o SPI estiver ligado, o pino fica ocupado e o clique não funciona. Por
> isso o RFID vem **desligado** por padrão (`ENABLE_RFID = False`), o que
> mantém o SPI fechado e o GPIO 7 livre. Se o clique ainda não funcionar,
> desligue o SPI: `sudo sed -i 's/^dtparam=spi=on/#dtparam=spi=on/' /boot/config.txt && sudo reboot`.

### Som
- **Apito** (buzzer ativo, GPIO 12) ao coletar fruta.
- **Música alegre** (buzzer passivo, GPIO 4) ao bater o recorde.
- **Música triste e longa** (buzzer passivo, GPIO 4) ao perder.

---

## Testes

```bash
python3 tests/test_game_logic.py -v     # 31 testes, rodam sem hardware
# ou
python3 -m pytest tests/ -v
```

Para testar o jogo inteiro sem a placa:

```bash
cd src && python3 main.py --sim --windowed
```

---

## Documentação

O relatório completo está em `docs/relatorio.md`, com motivação, requisitos,
diagramas (fontes em D2), arquitetura física e de software, metodologia e
testes. Diagramas renderizados em `docs/figuras/`.

---

## Solução de problemas de hardware

Displays piscando, buzzer mudo, LED azul, joystick que não anda: ver
`docs/HARDWARE_TROUBLESHOOTING.md`. Resumo dos ajustes em `src/config.py`:

- **Displays com lixo:** ligue só UMA chave DIP de display e defina
  `EXCLUSIVE_FIXED_DEVICE = "display4"`.
- **LED azul piscar com o buzzer:** `BLUE_LED_MODE = "indicator"` (desliga
  os displays de shift register — eles dividem o GPIO 17 com o LED).
- **Joystick parado:** rode `cd src && python3 calibrar_joystick.py`.

## Licença

GNU GPLv3 — ver `LICENSE`.
