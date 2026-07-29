#!/usr/bin/env bash
# install.sh — Prepara a Raspberry Pi para rodar o Snake Pi.
# Uso:  chmod +x install.sh && ./install.sh
set -euo pipefail

echo "==> Snake Pi — instalação"

if ! grep -qi "raspbian\|debian" /etc/os-release 2>/dev/null; then
  echo "AVISO: isto não parece um Raspberry Pi OS. Seguindo mesmo assim."
fi

echo "==> Atualizando índice de pacotes..."
sudo apt-get update

echo "==> Instalando dependências..."
sudo apt-get install -y \
  python3-pygame python3-smbus2 python3-spidev \
  python3-gpiozero python3-lgpio i2c-tools python3-pip

echo "==> Instalando driver do RFID (mfrc522)..."
pip3 install --break-system-packages mfrc522 || \
  echo "AVISO: mfrc522 não instalou. O jogo roda sem RFID."

echo "==> Verificando I2C e SPI..."
if ! lsmod | grep -q i2c_dev; then
  echo "!! I2C parece desabilitado."
  echo "   Habilite: sudo raspi-config > Interface Options > I2C > Yes"
fi
if [ ! -e /dev/spidev0.0 ]; then
  echo "!! SPI parece desabilitado (necessário só para o RFID)."
  echo "   Habilite: sudo raspi-config > Interface Options > SPI > Yes"
fi

echo
echo "==> Dispositivos no barramento I2C:"
i2cdetect -y 1 || echo "   (não consegui ler o I2C)"
echo
echo "   Esperado: 0x48 (ADC ADS7830) e 0x27 ou 0x3f (LCD1602)"
echo
echo "==> Pronto. Próximos passos:"
echo "    1) python3 diagnostico_placa.py    # descobre a topologia do 74HC595"
echo "    2) ajuste BUS_TOPOLOGY no config.py conforme o resultado"
echo "    3) python3 main.py                 # joga!"
