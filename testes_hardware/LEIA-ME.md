# Testes de hardware

Rode cada um de dentro de `src/` (para achar os módulos):

```bash
cd ~/snake-v5/projeto/src
python3 ../testes_hardware/teste_4digitos.py   # score no display de 4 digitos
python3 ../testes_hardware/teste_joystick.py   # clique do joystick (GPIO 7)
python3 ../testes_hardware/teste_musica.py     # apito + melodias
```

Chaves DIP por teste:
- teste_4digitos: só o display de 4 dígitos ligado
- teste_musica: Active Buzzer + Passive Buzzer ligados
- teste_joystick: precisa do SPI DESLIGADO (senão GPIO 7 fica ocupado)
