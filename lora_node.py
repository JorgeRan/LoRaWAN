import time
import struct
import RPi.GPIO as GPIO
from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from abp_config import DEVADDR, NWKSKEY, APPSKEY

# SX1262 pin setup
RESET_PIN = 18
BUSY_PIN  = 20
IRQ_PIN   = 16
TXEN_PIN  = 6
RXEN_PIN  = -1

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.OUT)
GPIO.setup(BUSY_PIN, GPIO.IN)
GPIO.setup(IRQ_PIN, GPIO.IN)
GPIO.setup(TXEN_PIN, GPIO.OUT)
if RXEN_PIN != -1:
    GPIO.setup(RXEN_PIN, GPIO.OUT)

# ABP LoRaWAN
class LoRaWAN:
    def __init__(self):
        self.devaddr = DEVADDR
        self.nwkskey = NWKSKEY
        self.appskey = APPSKEY
        self.fcnt_up = 0

    def encrypt_payload(self, payload):
        # LoRaWAN AES-CTR encryption block
        block_a = b'\x01' + b'\x00'*4 + struct.pack('<I', self.fcnt_up) + b'\x00' + b'\x00'*8
        cipher = AES.new(self.appskey, AES.MODE_ECB)
        key_stream = cipher.encrypt(block_a)
        enc = bytes([_a ^ _b for _a, _b in zip(payload, key_stream[:len(payload)])])
        return enc

    def calculate_mic(self, msg):
        cmac = CMAC.new(self.nwkskey, ciphermod=AES)
        cmac.update(msg)
        return cmac.digest()[:4]

    def build_uplink(self, payload_bytes):
        mhdr = b'\x40'  # Unconfirmed Data Up
        fhdr = struct.pack('<I', int.from_bytes(self.devaddr, 'little')) + b'\x00'
        fport = b'\x01'
        enc_payload = self.encrypt_payload(payload_bytes)
        msg = mhdr + fhdr + fport + enc_payload
        mic = self.calculate_mic(msg)
        self.fcnt_up += 1
        return msg + mic

# Dummy SPI send/receive (replace with actual SX1262 HAL)
def sx1262_send(packet):
    print(f"[SX1262] Sending packet: {packet.hex()}")

# Node main loop
if __name__ == "__main__":
    lora = LoRaWAN()
    counter = 0

    try:
        while True:
            payload = struct.pack("<H", counter)  # Example: 2-byte counter
            uplink = lora.build_uplink(payload)
            sx1262_send(uplink)
            print(f"[Node] Sent uplink {counter}")
            counter += 1
            time.sleep(10)  # send every 10s
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Stopped")
