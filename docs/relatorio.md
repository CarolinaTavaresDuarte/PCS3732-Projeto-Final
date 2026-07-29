# Snake Pi — Relatório do Projeto

**Disciplina:** Laboratório de Processadores — Escola Politécnica da USP  
**Grupo:** _(preencher: integrantes e NUSP)_  
**Plataforma:** Raspberry Pi 4 + Freenove Projects Board for Raspberry Pi v1.2

> Base para a versão final em LaTeX (Overleaf).

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

## 3. Requisitos Funcionais

_(mantém a mesma tabela da versão anterior, atualizada conforme a implementação do grupo.)_

## 4. Requisitos Não Funcionais

Atualizar o RNF10 para:

> Atualização estável do dispositivo selecionado no barramento 74HC595,
> respeitando as limitações de multiplexação da plataforma.

---

## 5. Diagramas

- Arquitetura Física
- Arquitetura de Software
- Máquina de Estados
- **Diagrama de Sequência**

### 5.4 Diagrama de sequência

O diagrama de sequência apresenta o ciclo principal da partida, mostrando a
interação entre usuário, laço principal, GameEngine, GameState, threads de
entrada/saída, renderizador e periféricos físicos.

---

## 6. Ferramentas

Manter a seção original.

---

## 7. Metodologia

Manter a seção original.

---

## 8. Testes

### Estratégia

- Testes unitários
- Testes de integração
- Testes em hardware

### Resultados

Foram executados **34 testes automatizados**, com **100% de aprovação**.

Completar a tabela dos testes físicos utilizando os resultados obtidos na
bancada.

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

- Freenove Projects Kit for Raspberry Pi.
- Documentação FNK0054.
- Datasheets ADS7830, 74HC595, HD44780 e MFRC522.
- Documentação Pygame, gpiozero e D2.

