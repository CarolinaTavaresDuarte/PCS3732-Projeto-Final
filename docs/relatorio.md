# Snake Pi — Relatório do Projeto

**Disciplina:** Laboratório de Processadores — Escola Politécnica da USP  
**Grupo:** _(Ana Paula Arejano 13680289
Carolina Tavares Duarte 12690963
Paulo Henrique Mota de Oliveira 14601816)_ 

**Plataforma:** Raspberry Pi 4 + Freenove Projects Board for Raspberry Pi v1.2

---

## 1. Motivação

O projeto Snake Pi integra lógica de jogo, concorrência e periféricos embarcados
da Freenove Projects Board em uma aplicação única. O objetivo foi explorar
barramentos I²C, SPI, GPIO e registradores de deslocamento (74HC595),
mantendo a lógica desacoplada do hardware e totalmente testável.

---

## 2. Objetivos

### Objetivo geral

Desenvolver uma versão do jogo Snake executada em Raspberry Pi 4, utilizando
o monitor HDMI como interface principal e os periféricos da placa Freenove
como interface física complementar.

### Objetivos específicos

1. Implementar a lógica do jogo de forma modular.
2. Integrar joystick, potenciômetro, LCD e RFID.
3. Controlar os dispositivos conectados ao 74HC595.
4. Utilizar threads para desacoplar periféricos.
5. Persistir ranking.
6. Implementar degradação graciosa.

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
| RF08 | Controle por joystick analógico, botões físicos e teclado | ✅ |
| RF09 | Exibição de pontuação e nível no LCD1602 | ✅ |
| RF10 | Seleção opcional de dificuldade por RFID | ✅ |
| RF11 | Efeitos sonoros distintos para eventos do jogo | ✅ |
| RF12 | Exibição de animações na matriz de LEDs 8×8 quando selecionada no barramento 74HC595 | ✅ |
| RF13 | Indicação de velocidade no bar graph | ✅ |
| RF14 | Exibição da pontuação no display de quatro dígitos quando selecionado no barramento 74HC595 | ✅ |
| RF15 | Comandos de pausa e reinício | ✅ |
| RF16 | Ajuste de velocidade pelo potenciômetro | ✅ |
| RF17 | Sistema de níveis com aumento progressivo de velocidade | ✅ |
| RF18 | Frutas especiais temporárias | ✅ |
| RF19 | Obstáculos definidos conforme a dificuldade | ✅ |
| RF20 | Ranking persistido em arquivo | ✅ |

## 4. Requisitos não funcionais

| ID | Requisito | Status |
|----|-----------|--------|
| RNF01 | Execução em Raspberry Pi OS Bookworm com Python 3.11 | ✅ |
| RNF02 | Renderização do jogo no monitor HDMI com taxa configurável de quadros | ✅ |
| RNF03 | Degradação graciosa: a ausência ou falha de um periférico não interrompe o jogo | ✅ |
| RNF04 | Código modular, organizado em camadas e com baixo acoplamento | ✅ |
| RNF05 | Lógica do jogo testável sem acesso ao hardware físico | ✅ |
| RNF06 | Pinagem e parâmetros de hardware centralizados em arquivo de configuração | ✅ |
| RNF07 | Uso de type hints, docstrings e organização compatível com PEP 8 | ✅ |
| RNF08 | Uso de concorrência sem bloquear o laço principal do jogo | ✅ |
| RNF09 | Encerramento limpo, com liberação dos recursos de GPIO | ✅ |
| RNF10 | Atualização estável do dispositivo selecionado no barramento 74HC595, respeitando as limitações físicas de multiplexação da placa | ✅ |

---
## 5. Diagramas da arquitetura

### 5.1 Arquitetura física

![Arquitetura física do sistema](figuras/arquitetura_fisica.svg)

### 5.2 Arquitetura de software

![Arquitetura de software do sistema](figuras/arquitetura_software.svg)

### 5.3 Máquina de estados

![Máquina de estados do sistema](figuras/maquina_estados.svg)

### 5.4 Diagrama de sequência

![Diagrama de sequência do ciclo principal da partida](figuras/diagrama_sequencia.svg)

O diagrama de sequência apresenta o ciclo principal da partida, mostrando a
interação entre usuário, laço principal, `GameEngine`, `GameState`, threads de
entrada e saída, renderizador e periféricos físicos.

---

## 6. Ferramentas utilizadas

### 6.1 Linguagens
- **Python 3.11** - aplicação completa
- **D2** - diagramas (fonte editável)
- **Markdown / LaTeX** - documentação

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

### 8.2 Rastreabilidade entre requisitos e testes

| Requisito | Caso de teste | Resultado |
|-----------|---------------|-----------|
| RF01 | `TestMenu::*` | ✅ |
| RF02, RF03 | `TestSnake::test_movimento`, `test_crescimento_preserva_cauda` | ✅ |
| RF04, RF18 | `TestFruit::*` | ✅ |
| RF05 | `TestEngine::test_morre_na_parede` | ✅ |
| RF06 | `TestSnake::test_colisao_consigo_mesma` | ✅ |
| RF07 | Testes de transição para `GAME_OVER` e reinício | ✅ |
| RF13, RF14 | `TestDisplays::*` | ✅ |
| RF16 | `TestEngine::test_potenciometro_altera_velocidade` | ✅ |
| RF17 | `TestEngine::test_dificuldades_tem_velocidades_distintas` | ✅ |
| RF19 | `TestBoard::test_obstaculos_respeitam_area_livre` | ✅ |
| RF20 | `TestScoreBoard::test_persistencia`, `test_ranking_ordenado_e_limitado` | ✅ |
| RNF03 | `test_arquivo_corrompido_nao_quebra` e testes de degradação graciosa | ✅ |
| RNF05 | Execução dos testes sem hardware físico | ✅ |

### 8.3 Testes de hardware

| Componente | Procedimento | Resultado |
|------------|--------------|-----------|
| Joystick analógico | Leitura dos canais 5 e 6 do ADS7830 | ✅ |
| Potenciômetro | Leitura pelo ADC e alteração da velocidade | ✅ |
| Botões físicos | Leitura dos GPIOs configurados | ✅ |
| LCD1602 | Exibição de pontuação e nível via I²C | ✅ |
| Buzzers | Reprodução dos efeitos sonoros | ✅ |
| Bar graph | Indicação física da velocidade | ✅ |
| Matriz 8×8 | Teste isolado no barramento 74HC595 | ✅ |
| Display de quatro dígitos | Teste isolado no barramento 74HC595 | ✅ |
| RFID | Leitura de cartões e seleção de dificuldade | ✅ |

Foram executados **34 testes automatizados**, com **100% de aprovação**. Reproduzir com:

```bash
python3 tests/test_game_logic.py -v
```

---

## 9. Conclusão

O projeto atingiu os objetivos propostos, integrando diferentes periféricos da
Freenove Projects Board em uma arquitetura modular, desacoplada e testável.
A utilização de concorrência permitiu separar a lógica principal das rotinas de
entrada e saída, mantendo o jogo responsivo mesmo na presença de periféricos
mais lentos.

Durante o desenvolvimento foram identificadas limitações físicas da placa,
especialmente relacionadas ao compartilhamento do barramento 74HC595 entre a
matriz de LEDs, o display de quatro dígitos e o bar graph. Essas restrições
foram tratadas por meio de configuração centralizada e degradação graciosa.

Os testes automatizados (34 casos) validaram a lógica do jogo, enquanto os
testes de bancada confirmaram o funcionamento dos periféricos suportados.

Como trabalhos futuros destacam-se novos modos de jogo, power-ups adicionais,
uso dos demais sensores da placa e expansão do sistema de ranking.

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


