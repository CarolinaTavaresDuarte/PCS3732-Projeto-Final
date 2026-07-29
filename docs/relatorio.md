# Snake Pi — Relatório do Projeto

**Disciplina:** Laboratório de Processadores — Escola Politécnica da USP
**Grupo:** _(preencher: integrantes e NUSP)_
**Plataforma:** Raspberry Pi 4 + Freenove Projects Board for Raspberry Pi v1.2

> **Nota sobre este documento.** Este é o relatório em Markdown, base para a
> versão final (Overleaf/LaTeX, máx. 20 páginas de conteúdo). As seções
> marcadas com _(preencher)_ dependem de dados do grupo (nomes, fotos da
> bancada, resultados finais, revisão por pares) e devem ser completadas ao
> longo das entregas semanais. As referências ao final ainda precisam ser
> formatadas em **ABNT**.

---

## 1. Motivação / Justificativa

O jogo Snake é um problema clássico e de escopo bem delimitado, o que o torna
um bom veículo para exercitar o objetivo central da disciplina: integrar um
processador embarcado a periféricos heterogêneos de entrada e saída. Em vez de
um sistema puramente digital na tela, o projeto obriga a lidar com conversão
analógico-digital (joystick e potenciômetro), barramentos seriais síncronos
(I²C, SPI), registradores de deslocamento (74HC595), atuadores (buzzers) e
concorrência real entre esses dispositivos.

A escolha por manter o jogo no monitor HDMI, com os periféricos físicos
espelhando o estado, permite explorar praticamente todos os componentes da
placa dentro de uma aplicação única e coesa — do ADC ao multiplexação de
displays — sem que nenhum deles seja um enfeite desconectado da lógica.

**Projetos similares:**
- Implementações de Snake em Raspberry Pi com matriz de LED _(preencher com links encontrados)_
- Exemplos oficiais da Freenove para a Projects Board (FNK0054)

---

## 2. Objetivos

### Objetivo geral

Desenvolver uma versão do jogo Snake executada integralmente em uma Raspberry
Pi 4, renderizada em monitor HDMI, integrando os periféricos da Freenove
Projects Board como interface física de entrada e saída.

### Objetivos específicos

1. Implementar a lógica completa do jogo (movimento, colisões, frutas, níveis,
   pontuação persistente) de forma independente de hardware e testável.
2. Ler entradas analógicas (joystick, potenciômetro) via ADC no barramento I²C.
3. Controlar múltiplos displays (LCD1602, matriz 8×8, bar graph, display de 4
   dígitos) que compartilham recursos de GPIO.
4. Selecionar a dificuldade por cartões RFID (SPI).
5. Fornecer retorno sonoro por buzzers ativo e passivo.
6. Aplicar concorrência (threads) para desacoplar periféricos lentos do laço
   principal do jogo.
7. Garantir robustez: o sistema deve continuar operando quando um periférico
   falha ou está ausente.

---

## 3. Requisitos funcionais

| ID | Requisito | Status |
|----|-----------|--------|
| RF01 | Menu inicial com Start Game, High Score, Configurações e Sair | ✅ |
| RF02 | Movimento da cobra em quatro direções | ✅ |
| RF03 | Crescimento ao comer fruta | ✅ |
| RF04 | Geração aleatória de frutas em célula livre | ✅ |
| RF05 | Detecção de colisão com parede | ✅ |
| RF06 | Detecção de colisão consigo mesma | ✅ |
| RF07 | Estado de Game Over e reinício | ✅ |
| RF08 | Controle por joystick analógico e por botões | ✅ |
| RF09 | Exibição de score e nível no LCD1602 | ✅ |
| RF10 | Seleção de dificuldade por RFID | ✅ |
| RF11 | Efeitos sonoros distintos por evento | ✅ |
| RF12 | Animações na matriz de LED 8×8 | ✅ |
| RF13 | Indicação de velocidade no bar graph | ✅ |
| RF14 | Exibição do score no display de 4 dígitos | ✅ |
| RF15 | Botão de pausa e de reinício | ✅ |
| RF16 | Ajuste de velocidade pelo potenciômetro | ✅ |
| RF17 | Sistema de níveis com aumento de velocidade | ✅ |
| RF18 | Frutas especiais temporárias | ✅ |
| RF19 | Obstáculos conforme dificuldade | ✅ |
| RF20 | Ranking persistido em arquivo | ✅ |

## 4. Requisitos não funcionais

| ID | Requisito |
|----|-----------|
| RNF01 | Executar em Raspberry Pi OS Bookworm, Python 3.11 |
| RNF02 | Renderização a 60 fps no monitor HDMI |
| RNF03 | Degradação graciosa: periférico ausente não interrompe o jogo |
| RNF04 | Código modular em camadas, com baixo acoplamento |
| RNF05 | Lógica de jogo testável sem hardware |
| RNF06 | Toda a pinagem centralizada em um único arquivo de configuração |
| RNF07 | Aderência a PEP 8, com type hints e docstrings |
| RNF08 | Concorrência sem travamento do laço principal |
| RNF09 | Encerramento limpo, liberando GPIOs |
| RNF10 | Multiplexação dos displays sem cintilação perceptível (> 200 Hz) |

---

## 5. Diagramas da arquitetura

Fontes editáveis em `docs/diagramas/*.d2`; figuras renderizadas em
`docs/figuras/*.svg`.

- **Arquitetura de software** — `arquitetura_software.d2`
- **Arquitetura física** — `arquitetura_fisica.d2`
- **Máquina de estados (comportamental)** — `maquina_estados.d2`

### 5.1 Arquitetura física

O sistema é composto pela Raspberry Pi 4 acoplada à Freenove Projects Board.
A saída de vídeo é HDMI. Os periféricos se distribuem em quatro grupos de
comunicação:

- **I²C-1** (GPIO 2/3): ADS7830 (`0x48`) para joystick e potenciômetro;
  LCD1602 (`0x27`).
- **SPI0** (GPIO 8–11): leitor RFID MFRC522.
- **74HC595** (GPIO 22/27/17): matriz 8×8, bar graph e display de 4 dígitos,
  que compartilham o mesmo barramento serial.
- **GPIO diretos**: botão do joystick (7), botões coloridos (20, 21, 26, 16),
  buzzer ativo (12) e passivo (4).

### 5.2 Arquitetura de software (modelagem estática)

Cinco camadas com dependências unidirecionais. A camada de lógica não conhece
Pygame nem GPIO; a de hardware não conhece as regras do jogo. O acoplamento é
feito por injeção de dependência em `main.py`.

### 5.3 Modelagem comportamental

Máquina de estados finita: MENU, PLAYING, PAUSED, GAME_OVER, HIGH_SCORES,
SETTINGS, QUIT. As transições são disparadas por eventos de entrada (joystick,
botões, teclado) e por eventos internos do jogo (colisão).

---

## 6. Ferramentas utilizadas

### 6.1 Linguagens
- **Python 3.11** — aplicação completa
- **D2** — diagramas (fonte editável)
- **Markdown / LaTeX** — documentação

### 6.2 Bibliotecas / Frameworks
| Biblioteca | Uso |
|-----------|-----|
| pygame | Renderização do jogo no HDMI |
| gpiozero | Abstração de GPIO (botões, buzzers, 74HC595) |
| lgpio | Backend de GPIO no Bookworm |
| smbus2 / smbus | I²C (ADS7830 e LCD1602) |
| spidev | SPI (RFID) |
| mfrc522 | Driver do leitor RC522 |
| unittest | Testes automatizados |

### 6.3 Hardware
- Raspberry Pi 4 Model B
- Freenove Projects Board for Raspberry Pi v1.2 (FNK0054)
- ADS7830 (ADC I²C), LCD1602 (I²C), MFRC522 (SPI)
- 74HC595 (registradores de deslocamento), matriz 8×8, bar graph, display 4
  dígitos, joystick analógico, potenciômetro, buzzers ativo e passivo,
  botões, monitor HDMI, fonte 5 V/3 A.

---

## 7. Metodologia de desenvolvimento

O desenvolvimento seguiu abordagem incremental, com o versionamento no GitHub
e entregas semanais (Releases). A lógica do jogo foi construída primeiro e de
forma isolada do hardware, o que permitiu validá-la por testes automatizados
antes mesmo de ligar a placa. Em seguida foram implementados os drivers de
hardware, um a um, cada qual com um modo de simulação para permitir testes sem
o dispositivo físico.

Uma decisão metodológica central foi **investigar a placa real antes de fixar
a pinagem**: a pinagem foi extraída do código oficial da Freenove e validada
com um script de diagnóstico (`src/diagnostico_placa.py`), o que revelou
restrições de hardware (barramento 74HC595 compartilhado, conflito do GPIO 7
com o SPI) que orientaram a arquitetura.

Práticas adotadas: commits incrementais, uso de branches e Pull Requests,
revisão por pares (GitHub Issues, Semana 2), e centralização da configuração
para isolar mudanças de hardware.

---

## 8. Testes planejados / Resultados obtidos

### 8.1 Estratégia

A validação combina três níveis: testes automatizados da lógica pura (rodam em
qualquer máquina), teste ponta-a-ponta em modo simulação (exercita as threads
e a máquina de estados) e testes manuais de hardware na bancada (script de
diagnóstico).

### 8.2 Rastreabilidade requisito ↔ teste

| Requisito | Caso de teste | Resultado |
|-----------|---------------|-----------|
| RF02, RF03 | `TestSnake::test_movimento`, `test_crescimento_preserva_cauda` | ✅ |
| RF05 | `TestEngine::test_morre_na_parede` | ✅ |
| RF06 | `TestSnake::test_colisao_consigo_mesma` | ✅ |
| RF04, RF18 | `TestFruit::*` | ✅ |
| RF17 | `TestEngine::test_dificuldades_tem_velocidades_distintas` | ✅ |
| RF16 | `TestEngine::test_potenciometro_altera_velocidade` | ✅ |
| RF19 | `TestBoard::test_obstaculos_respeitam_area_livre` | ✅ |
| RF20 | `TestScoreBoard::test_persistencia`, `test_ranking_ordenado_e_limitado` | ✅ |
| RF01 | `TestMenu::*` | ✅ |
| RF13, RF14 | `TestDisplays::*` | ✅ |
| RNF03 | `test_arquivo_corrompido_nao_quebra` + degradação graciosa | ✅ |

### 8.3 Resultados dos testes automatizados

31 testes, 100% aprovados. Reproduzir com:

```bash
python3 tests/test_game_logic.py -v
```

### 8.4 Testes de hardware (bancada)

| Teste | Método | Resultado |
|-------|--------|-----------|
| Botões coloridos (D-pad) | `diagnostico_placa.py` teste 3 | GPIO 20, 21, 26 confirmados _(preencher 16)_ |
| Buzzers | `diagnostico_placa.py` teste 4 | _(preencher)_ |
| Topologia 74HC595 | `diagnostico_placa.py` teste 5 | _(preencher: cascata ou exclusivo)_ |
| I²C (ADC + LCD) | `i2cdetect -y 1` | _(preencher)_ |

_(Anexar fotos da bancada em `docs/figuras/`.)_

---

## 9. Conclusões

_(A completar na entrega final.)_ Esta seção deve refletir sobre:

- **Objetivos cumpridos:** quais dos objetivos específicos da Seção 2 foram
  atingidos e em que grau.
- **Requisitos satisfeitos:** confrontar com as tabelas das Seções 3 e 4.
- **Dificuldades encontradas:** o barramento 74HC595 compartilhado entre três
  displays; o conflito do GPIO 7 (botão do joystick) com o CE1 do SPI ao
  habilitar o RFID; a configuração de I²C/SPI no Bookworm.
- **Lições aprendidas:** a importância de investigar o hardware real antes de
  fixar a pinagem; o valor de manter a lógica testável sem hardware.
- **Trabalhos futuros:** modo dois jogadores, power-ups, uso de termistor e
  fotorresistor, ranking com iniciais pelo keypad.

---

## Referências

_(Formatar em ABNT.)_

- FREENOVE. _Freenove Projects Kit for Raspberry Pi_. Disponível em:
  https://github.com/Freenove/Freenove_Projects_Kit_for_Raspberry_Pi
- FREENOVE. _Documentação FNK0054_. Disponível em:
  https://docs.freenove.com/projects/fnk0054/en/latest/
- Documentação do gpiozero, Pygame, D2.
- Datasheets: ADS7830 (Texas Instruments), 74HC595 (NXP), HD44780 (Hitachi),
  MFRC522 (NXP).
