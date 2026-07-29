# Solução de problemas de hardware (v4)

Guia focado nos quatro sintomas mais comuns na bancada e no que muda no
`src/config.py` para resolver cada um.

## 1. Displays (matriz, 4 dígitos, bar graph) piscando sem imagem nítida

Duas causas somadas, ambas tratadas na v4.

### a) Multiplexação lenta (corrigido no código)
A v4 varre todas as colunas/dígitos num laço contínuo (como o código de
referência da Freenove), em vez de uma por vez. Isso sozinho elimina o
tremor de um display corretamente ligado. Nada a fazer.

### b) Barramento 74HC595 compartilhado (ação sua)
Matriz, bar graph e display de 4 dígitos usam os MESMOS pinos (22/27/17).
Se você ligar a chave DIP de mais de um ao mesmo tempo, todos recebem os
mesmos bytes e mostram lixo.

**Solução simples:** ligue a chave DIP de UM só (sugestão: o de 4 dígitos,
que mostra o score) e em `src/config.py`:

```python
EXCLUSIVE_FIXED_DEVICE: str | None = "display4"   # ou "matrix" / "bargraph"
```

Se o seu diagnóstico (teste 5) mostrou que os três estão em CASCATA, então
troque para:

```python
BUS_TOPOLOGY: BusTopology = BusTopology.CASCADE
```

e aí os três funcionam juntos, sem precisar do `EXCLUSIVE_FIXED_DEVICE`.

## 2. Buzzer ativo (GPIO 12) sem som

O código está correto (igual ao exemplo da Freenove). Se não sai som:

- **Chave DIP "3-Active Buzzer" ligada?** É a causa mais comum.
- **GPIO 12 é compartilhado com o relé.** Desligue a chave DIP do relé.
- Confirme no log (`src/snake_pi.log`) a linha `Buzzers prontos`. Se
  aparecer `Buzzer ativo indisponível`, o pino está ocupado — feche outros
  programas (`pkill -f main.py`).

## 3. LED azul (GPIO 17) piscar junto com o buzzer

**Conflito de hardware:** o GPIO 17 é, na placa, o LED azul E o clock dos
74HC595. É impossível usar os dois ao mesmo tempo. Você escolhe:

```python
# src/config.py
BLUE_LED_MODE: str = "clock"      # displays funcionam; LED não é controlável
BLUE_LED_MODE: str = "indicator"  # LED pisca com o buzzer; displays DESLIGADOS
```

No modo `indicator`, a matriz, o bar graph e o display de 4 dígitos ficam
desligados de propósito — o score continua no monitor e no LCD.

## 4. Joystick não anda em nenhuma direção

As direções vêm do **ADC (canais 5 e 6, via I²C)**, não do GPIO 7 — este é
só o botão. "Não anda" quase sempre significa que o ADC não está sendo lido.

Rode a calibração:

```bash
cd src
python3 calibrar_joystick.py
```

Ela diz na hora se o problema é o I²C (ADC mudo) ou calibração, e sugere os
valores de `JOY_CENTER` e `JOY_DEADZONE` para colar no config.

Se o ADC estiver mudo:
- a chave POWER da placa está ligada?
- `i2cdetect -y 1` mostra o endereço `48`?
- I²C habilitado? (`dtparam=i2c_arm=on` no `config.txt`)

Enquanto o I²C não voltar, use os **botões coloridos** como direcional —
eles não dependem do I²C.

---

## Atualização v4.2 — LEDs acesos 100% sem mostrar nada

Sintoma diferente do flicker: os LEDs ficam todos acesos. Eram dois bugs de
polaridade no código, agora corrigidos:

- **Bar graph** estava invertido (assumia que 0 acende; na placa 1 acende).
  Com a barra vazia, mandava tudo 1 → todos acesos. Corrigido.
- **Display de 4 dígitos** tinha os dois bytes trocados (segmentos e seleção
  de dígito). Corrigido para a ordem da Freenove.

### Abordagem recomendada para os LEDs físicos

Dos três displays, só o **bar graph** não precisa de multiplexação — são 10
LEDs estáticos. Por isso ele é o único que fica **estável** em Python, sem
cintilação. A matriz e o display de 4 dígitos dependem de multiplexação, que
o Python não sustenta com tempo preciso.

Recomendação: use o bar graph como indicador físico principal (mostra a
velocidade). No `src/config.py` já vem:

```python
EXCLUSIVE_FIXED_DEVICE: str | None = "bargraph"
```

Ligue só a chave DIP do LED Bar Graph. Para testar cada display isolado:

```bash
cd src
python3 teste_display.py barra      # bar graph (estável)
python3 teste_display.py 4digitos   # multiplexado
python3 teste_display.py matriz     # multiplexado
```
