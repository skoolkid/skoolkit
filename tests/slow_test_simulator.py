from skoolkittest import SkoolKitTestCase
from skoolkit import CSimulator
from skoolkit.simulator import Simulator, F, SP, PC
from sim_test_tracers import *

class ROMReadOnlyTest(SkoolKitTestCase):
    def _get_simulator(self, memory):
        simulator = Simulator(memory, config={'c': CSimulator})
        if CSimulator:
            return CSimulator(simulator), simulator.memory, simulator.registers
        return simulator, simulator.memory, simulator.registers

    def _test_read_only(self, code, start, value=0):
        start = 0x8000
        stop = 0x8000 + len(code)
        memory = [value] * 65536
        memory[start:stop] = code
        simulator = Simulator(memory, config={'c': CSimulator})
        if CSimulator:
            CSimulator(simulator).run(start, stop)
        else:
            simulator.run(start, stop)
        self.assertTrue(all(b == value for b in simulator.memory[:0x4000]))

    def test_ld_8_bit(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0x11, 0x00, 0x00,       # $8003 LD DE,$0000
            0x01, 0x00, 0x00,       # $8006 LD BC,$0000
            0xDD, 0x21, 0x00, 0x00, # $8009 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $800D LD IY,$0000
            0x3E, 0xAA,             # $8011 LD A,$AA
            0x22, 0x17, 0x80,       # $8013 LD ($8017),HL
            0x32, 0x00, 0x00,       # $8016 LD ($0000),A
            0x02,                   # $8019 LD (BC),A
            0x12,                   # $801A LD (DE),A
            0x70,                   # $801B LD (HL),B
            0x71,                   # $801C LD (HL),C
            0x72,                   # $801D LD (HL),D
            0x73,                   # $801E LD (HL),E
            0x74,                   # $801F LD (HL),H
            0x75,                   # $8020 LD (HL),L
            0x77,                   # $8021 LD (HL),A
            0x36, 0xAA,             # $8022 LD (HL),$AA
            0xDD, 0x70, 0x00,       # $8024 LD (IX+$00),B
            0xDD, 0x71, 0x00,       # $8027 LD (IX+$00),C
            0xDD, 0x72, 0x00,       # $802A LD (IX+$00),D
            0xDD, 0x73, 0x00,       # $802D LD (IX+$00),E
            0xDD, 0x74, 0x00,       # $8030 LD (IX+$00),H
            0xDD, 0x75, 0x00,       # $8033 LD (IX+$00),L
            0xDD, 0x77, 0x00,       # $8036 LD (IX+$00),A
            0xDD, 0x36, 0x00, 0xAA, # $8039 LD (IX+$00),$AA
            0xFD, 0x70, 0x00,       # $803D LD (IY+$00),B
            0xFD, 0x71, 0x00,       # $8040 LD (IY+$00),C
            0xFD, 0x72, 0x00,       # $8043 LD (IY+$00),D
            0xFD, 0x73, 0x00,       # $8046 LD (IY+$00),E
            0xFD, 0x74, 0x00,       # $8049 LD (IY+$00),H
            0xFD, 0x75, 0x00,       # $804C LD (IY+$00),L
            0xFD, 0x77, 0x00,       # $804F LD (IY+$00),A
            0xFD, 0x36, 0x00, 0xAA, # $8052 LD (IY+$00),$AA
            0x23,                   # $8056 INC HL
            0x13,                   # $8057 INC DE
            0x03,                   # $8058 INC BC
            0xDD, 0x23,             # $8059 INC IX
            0xFD, 0x23,             # $805B INC IY
            0xCB, 0x74,             # $805D BIT 6,H
            0x28, 0xB0,             # $805F JR Z,$8011
        )
        self._test_read_only(code, 0x8000)

    def test_inc(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0x34,                   # $800B INC (HL)
            0xDD, 0x34, 0x00,       # $800C INC (IX+$00)
            0xFD, 0x34, 0x00,       # $800F INC (IY+$00)
            0x23,                   # $8012 INC HL
            0xDD, 0x23,             # $8013 INC IX
            0xFD, 0x23,             # $8015 INC IY
            0xCB, 0x74,             # $8017 BIT 6,H
            0x28, 0xF0,             # $8019 JR Z,$800B
        )
        self._test_read_only(code, 0x8000)

    def test_dec(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0x35,                   # $800B DEC (HL)
            0xDD, 0x35, 0x00,       # $800C DEC (IX+$00)
            0xFD, 0x35, 0x00,       # $800F DEC (IY+$00)
            0x23,                   # $8012 INC HL
            0xDD, 0x23,             # $8013 INC IX
            0xFD, 0x23,             # $8015 INC IY
            0xCB, 0x74,             # $8017 BIT 6,H
            0x28, 0xF0,             # $8019 JR Z,$800B
        )
        self._test_read_only(code, 0x8000)

    def test_shift_left(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0xCB, 0x26,             # $800B SLA (HL)
            0xCB, 0x36,             # $800D SLL (HL)
            0xDD, 0xCB, 0x00, 0x26, # $800F SLA (IX+$00)
            0xDD, 0xCB, 0x00, 0x36, # $8013 SLL (IX+$00)
            0xFD, 0xCB, 0x00, 0x26, # $8017 SLA (IY+$00)
            0xFD, 0xCB, 0x00, 0x36, # $801B SLL (IY+$00)
            0x23,                   # $801F INC HL
            0xDD, 0x23,             # $8020 INC IX
            0xFD, 0x23,             # $8022 INC IY
            0xCB, 0x74,             # $8024 BIT 6,H
            0x28, 0xE3,             # $8026 JR Z,$800B
        )
        self._test_read_only(code, 0x8000, 0x01)

    def test_shift_right(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0xCB, 0x2E,             # $800B SRA (HL)
            0xCB, 0x3E,             # $800D SRL (HL)
            0xDD, 0xCB, 0x00, 0x2E, # $800F SRA (IX+$00)
            0xDD, 0xCB, 0x00, 0x3E, # $8013 SRL (IX+$00)
            0xFD, 0xCB, 0x00, 0x2E, # $8017 SRA (IY+$00)
            0xFD, 0xCB, 0x00, 0x3E, # $801B SRL (IY+$00)
            0x23,                   # $801F INC HL
            0xDD, 0x23,             # $8020 INC IX
            0xFD, 0x23,             # $8022 INC IY
            0xCB, 0x74,             # $8024 BIT 6,H
            0x28, 0xE3,             # $8026 JR Z,$800B
        )
        self._test_read_only(code, 0x8000, 0x80)

    def test_rotate_left(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0xCB, 0x06,             # $800B RLC (HL)
            0xCB, 0x16,             # $800D RL (HL)
            0xDD, 0xCB, 0x00, 0x06, # $800F RLC (IX+$00)
            0xDD, 0xCB, 0x00, 0x16, # $8013 RL (IX+$00)
            0xFD, 0xCB, 0x00, 0x06, # $8017 RLC (IY+$00)
            0xFD, 0xCB, 0x00, 0x16, # $801B RL (IY+$00)
            0x23,                   # $801F INC HL
            0xDD, 0x23,             # $8020 INC IX
            0xFD, 0x23,             # $8022 INC IY
            0xCB, 0x74,             # $8024 BIT 6,H
            0x28, 0xE3,             # $8026 JR Z,$800B
        )
        self._test_read_only(code, 0x8000, 0x01)

    def test_rotate_right(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0xCB, 0x0E,             # $800B RRC (HL)
            0xCB, 0x1E,             # $800D RR (HL)
            0xDD, 0xCB, 0x00, 0x0E, # $800F RRC (IX+$00)
            0xDD, 0xCB, 0x00, 0x1E, # $8013 RR (IX+$00)
            0xFD, 0xCB, 0x00, 0x0E, # $8017 RRC (IY+$00)
            0xFD, 0xCB, 0x00, 0x1E, # $801B RR (IY+$00)
            0x23,                   # $801F INC HL
            0xDD, 0x23,             # $8020 INC IX
            0xFD, 0x23,             # $8022 INC IY
            0xCB, 0x74,             # $8024 BIT 6,H
            0x28, 0xE3,             # $8026 JR Z,$800B
        )
        self._test_read_only(code, 0x8000, 0x80)

    def test_res(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0xCB, 0xBE,             # $800B RES 7,(HL)
            0xCB, 0xB6,             # $800D RES 6,(HL)
            0xCB, 0xAE,             # $800F RES 5,(HL)
            0xCB, 0xA6,             # $8011 RES 4,(HL)
            0xCB, 0x9E,             # $8013 RES 3,(HL)
            0xCB, 0x96,             # $8015 RES 2,(HL)
            0xCB, 0x8E,             # $8017 RES 1,(HL)
            0xCB, 0x86,             # $8019 RES 0,(HL)
            0xDD, 0xCB, 0x00, 0xBE, # $801B RES 7,(IX+$00)
            0xDD, 0xCB, 0x00, 0xB6, # $801F RES 6,(IX+$00)
            0xDD, 0xCB, 0x00, 0xAE, # $8023 RES 5,(IX+$00)
            0xDD, 0xCB, 0x00, 0xA6, # $8027 RES 4,(IX+$00)
            0xDD, 0xCB, 0x00, 0x9E, # $802B RES 3,(IX+$00)
            0xDD, 0xCB, 0x00, 0x96, # $802F RES 2,(IX+$00)
            0xDD, 0xCB, 0x00, 0x8E, # $8033 RES 1,(IX+$00)
            0xDD, 0xCB, 0x00, 0x86, # $8037 RES 0,(IX+$00)
            0xFD, 0xCB, 0x00, 0xBE, # $803B RES 7,(IY+$00)
            0xFD, 0xCB, 0x00, 0xB6, # $803F RES 6,(IY+$00)
            0xFD, 0xCB, 0x00, 0xAE, # $8043 RES 5,(IY+$00)
            0xFD, 0xCB, 0x00, 0xA6, # $8047 RES 4,(IY+$00)
            0xFD, 0xCB, 0x00, 0x9E, # $804B RES 3,(IY+$00)
            0xFD, 0xCB, 0x00, 0x96, # $804F RES 2,(IY+$00)
            0xFD, 0xCB, 0x00, 0x8E, # $8053 RES 1,(IY+$00)
            0xFD, 0xCB, 0x00, 0x86, # $8057 RES 0,(IY+$00)
            0x23,                   # $805B INC HL
            0xDD, 0x23,             # $805C INC IX
            0xFD, 0x23,             # $805E INC IY
            0xCB, 0x74,             # $8060 BIT 6,H
            0x28, 0xA7,             # $8062 JR Z,$800B
        )
        self._test_read_only(code, 0x8000, 0xFF)

    def test_set(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0xDD, 0x21, 0x00, 0x00, # $8003 LD IX,$0000
            0xFD, 0x21, 0x00, 0x00, # $8007 LD IY,$0000
            0xCB, 0xFE,             # $800B SET 7,(HL)
            0xCB, 0xF6,             # $800D SET 6,(HL)
            0xCB, 0xEE,             # $800F SET 5,(HL)
            0xCB, 0xE6,             # $8011 SET 4,(HL)
            0xCB, 0xDE,             # $8013 SET 3,(HL)
            0xCB, 0xD6,             # $8015 SET 2,(HL)
            0xCB, 0xCE,             # $8017 SET 1,(HL)
            0xCB, 0xC6,             # $8019 SET 0,(HL)
            0xDD, 0xCB, 0x00, 0xFE, # $801B SET 7,(IX+$00)
            0xDD, 0xCB, 0x00, 0xF6, # $801F SET 6,(IX+$00)
            0xDD, 0xCB, 0x00, 0xEE, # $8023 SET 5,(IX+$00)
            0xDD, 0xCB, 0x00, 0xE6, # $8027 SET 4,(IX+$00)
            0xDD, 0xCB, 0x00, 0xDE, # $802B SET 3,(IX+$00)
            0xDD, 0xCB, 0x00, 0xD6, # $802F SET 2,(IX+$00)
            0xDD, 0xCB, 0x00, 0xCE, # $8033 SET 1,(IX+$00)
            0xDD, 0xCB, 0x00, 0xC6, # $8037 SET 0,(IX+$00)
            0xFD, 0xCB, 0x00, 0xFE, # $803B SET 7,(IY+$00)
            0xFD, 0xCB, 0x00, 0xF6, # $803F SET 6,(IY+$00)
            0xFD, 0xCB, 0x00, 0xEE, # $8043 SET 5,(IY+$00)
            0xFD, 0xCB, 0x00, 0xE6, # $8047 SET 4,(IY+$00)
            0xFD, 0xCB, 0x00, 0xDE, # $804B SET 3,(IY+$00)
            0xFD, 0xCB, 0x00, 0xD6, # $804F SET 2,(IY+$00)
            0xFD, 0xCB, 0x00, 0xCE, # $8053 SET 1,(IY+$00)
            0xFD, 0xCB, 0x00, 0xC6, # $8057 SET 0,(IY+$00)
            0x23,                   # $805B INC HL
            0xDD, 0x23,             # $805C INC IX
            0xFD, 0x23,             # $805E INC IY
            0xCB, 0x74,             # $8060 BIT 6,H
            0x28, 0xA7,             # $8062 JR Z,$800B
        )
        self._test_read_only(code, 0x8000)

    def test_rld(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0x3E, 0xFF,             # $8003 LD A,$FF
            0xED, 0x6F,             # $8005 RLD
            0x23,                   # $8007 INC HL
            0xCB, 0x74,             # $8008 BIT 6,H
            0x28, 0xF7,             # $800A JR Z,$8003
        )
        self._test_read_only(code, 0x8000)

    def test_rrd(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0x3E, 0xFF,             # $8003 LD A,$FF
            0xED, 0x67,             # $8005 RRD
            0x23,                   # $8007 INC HL
            0xCB, 0x74,             # $8008 BIT 6,H
            0x28, 0xF7,             # $800A JR Z,$8003
        )
        self._test_read_only(code, 0x8000)

    def test_ldi(self):
        code = (
            0x11, 0x00, 0x00,       # $8000 LD DE,$0000
            0x21, 0x00, 0x80,       # $8003 LD HL,$8000
            0xED, 0xA0,             # $8006 LDI
            0xCB, 0x72,             # $8008 BIT 6,D
            0x28, 0xF7,             # $800A JR Z,$8003
        )
        self._test_read_only(code, 0x8000)

    def test_ldd(self):
        code = (
            0x11, 0xFF, 0x3F,       # $8000 LD DE,$3FFF
            0x21, 0x00, 0x80,       # $8003 LD HL,$8000
            0xED, 0xA8,             # $8006 LDD
            0xCB, 0x7A,             # $8008 BIT 7,D
            0x28, 0xF7,             # $800A JR Z,$8003
        )
        self._test_read_only(code, 0x8000)

    def test_ldir(self):
        code = (
            0x21, 0x00, 0xC0,       # $8000 LD HL,$C000
            0x11, 0x00, 0x00,       # $8003 LD DE,$0000
            0x01, 0x00, 0x40,       # $8006 LD BC,$4000
            0xED, 0xB0,             # $8009 LDIR
        )
        start = 0x8000
        stop = 0x8000 + len(code)
        memory = [0] * 65536
        memory[start:stop] = code
        memory[0xC000:] = [0xFF] * 0x4000
        simulator, memory, registers = self._get_simulator(memory)
        simulator.run(start, stop)
        self.assertTrue(all(b == 0 for b in memory[:0x4000]))

    def test_lddr(self):
        code = (
            0x21, 0xFF, 0xFF,       # $8000 LD HL,$FFFF
            0x11, 0xFF, 0x3F,       # $8003 LD DE,$3FFF
            0x01, 0x00, 0x40,       # $8006 LD BC,$4000
            0xED, 0xB8,             # $8009 LDDR
        )
        start = 0x8000
        stop = 0x8000 + len(code)
        memory = [0] * 65536
        memory[start:stop] = code
        memory[0xC000:] = [0xFF] * 0x4000
        simulator, memory, registers = self._get_simulator(memory)
        simulator.run(start, stop)
        self.assertTrue(all(b == 0 for b in memory[:0x4000]))

    def test_call(self):
        simulator, memory, registers = self._get_simulator([0] * 65536)
        for sp in range(1, 16386):
            for opcode, f in (
                    (0xC4, 0b00000000), # CALL NZ
                    (0xCC, 0b01000000), # CALL Z
                    (0xCD, 0b00000000), # CALL
                    (0xD4, 0b00000000), # CALL NC
                    (0xDC, 0b00000001), # CALL C
                    (0xE4, 0b00000000), # CALL PO
                    (0xEC, 0b00000100), # CALL PE
                    (0xF4, 0b00000000), # CALL P
                    (0xFC, 0b10000000), # CALL M
            ):
                memory[0x8000] = opcode
                registers[SP] = sp
                registers[F] = f
                simulator.run(0x8000)
                self.assertEqual(registers[PC], 0)
                if sp > 1:
                    self.assertEqual(memory[sp - 2], 0)
                if sp < 16385:
                    self.assertEqual(memory[sp - 1], 0)

    def test_ex_sp(self):
        code = (
            0x31, 0x00, 0x00,       # $8000 LD SP,$0000
            0x21, 0xFF, 0xFF,       # $8003 LD HL,$FFFF
            0xDD, 0x21, 0xFF, 0xFF, # $8006 LD IX,$FFFF
            0xFD, 0x21, 0xFF, 0xFF, # $800A LD IY,$FFFF
            0xE3,                   # $800E EX (SP),HL
            0xDD, 0xE3,             # $800F EX (SP),IX
            0xFD, 0xE3,             # $8011 EX (SP),IY
            0x33,                   # $8013 INC SP
            0x21, 0x00, 0x40,       # $8014 LD HL,$4000
            0xA7,                   # $8017 AND A
            0xED, 0x72,             # $8018 SBC HL,SP
            0x20, 0xE7,             # $801A JR NZ,$8003
        )
        self._test_read_only(code, 0x8000)

    def test_ld_16_bit(self):
        code = (
            0x21, 0x00, 0x00,       # $8000 LD HL,$0000
            0x22, 0x2E, 0x80,       # $8003 LD ($802E),HL
            0x22, 0x32, 0x80,       # $8006 LD ($8032),HL
            0x22, 0x35, 0x80,       # $8009 LD ($8035),HL
            0x22, 0x39, 0x80,       # $800C LD ($8039),HL
            0x22, 0x3D, 0x80,       # $800F LD ($803D),HL
            0x22, 0x41, 0x80,       # $8012 LD ($8041),HL
            0x22, 0x45, 0x80,       # $8015 LD ($8045),HL
            0x01, 0xFF, 0xFF,       # $8018 LD BC,$FFFF
            0x11, 0xFF, 0xFF,       # $801B LD DE,$FFFF
            0x21, 0xFF, 0xFF,       # $801E LD HL,$FFFF
            0x31, 0xFF, 0xFF,       # $8021 LD SP,$FFFF
            0xDD, 0x21, 0xFF, 0xFF, # $8024 LD IX,$FFFF
            0xFD, 0x21, 0xFF, 0xFF, # $8028 LD IY,$FFFF
            0xED, 0x43, 0x00, 0x00, # $802C LD ($0000),BC
            0xED, 0x53, 0x00, 0x00, # $8030 LD ($0000),DE
            0x22, 0x00, 0x00,       # $8034 LD ($0000),HL
            0xED, 0x73, 0x00, 0x00, # $8037 LD ($0000),SP
            0xDD, 0x22, 0x00, 0x00, # $803B LD ($0000),IX
            0xFD, 0x22, 0x00, 0x00, # $803F LD ($0000),IY
            0xED, 0x63, 0x00, 0x00, # $8043 LD ($0000),HL
            0x2A, 0x01, 0x80,       # $8047 LD HL,($8001)
            0x23,                   # $804A INC HL
            0x22, 0x01, 0x80,       # $804B LD ($8001),HL
            0xCB, 0x74,             # $804E BIT 6,H
            0x28, 0xAE,             # $8050 JR Z,$8000
        )
        self._test_read_only(code, 0x8000)

    def test_push(self):
        code = (
            0x21, 0x01, 0x00,       # $8000 LD HL,$0001
            0x22, 0x1A, 0x80,       # $8003 LD ($801A),HL
            0x37,                   # $8006 SCF
            0x9F,                   # $8007 SBC A,A
            0x01, 0xFF, 0xFF,       # $8008 LD BC,$FFFF
            0x11, 0xFF, 0xFF,       # $800B LD DE,$FFFF
            0x21, 0xFF, 0xFF,       # $800E LD HL,$FFFF
            0xDD, 0x21, 0xFF, 0xFF, # $8011 LD IX,$FFFF
            0xFD, 0x21, 0xFF, 0xFF, # $8015 LD IY,$FFFF
            0x31, 0x00, 0x00,       # $8019 LD SP,$0000
            0xF5,                   # $801C PUSH AF
            0xED, 0x7B, 0x1A, 0x80, # $801D LD SP,($801A)
            0xC5,                   # $8021 PUSH BC
            0xED, 0x7B, 0x1A, 0x80, # $8022 LD SP,($801A)
            0xD5,                   # $8026 PUSH DE
            0xED, 0x7B, 0x1A, 0x80, # $8027 LD SP,($801A)
            0xE5,                   # $802B PUSH HL
            0xED, 0x7B, 0x1A, 0x80, # $802C LD SP,($801A)
            0xDD, 0xE5,             # $8030 PUSH IX
            0xED, 0x7B, 0x1A, 0x80, # $8032 LD SP,($801A)
            0xFD, 0xE5,             # $8036 PUSH IY
            0x2A, 0x1A, 0x80,       # $8038 LD HL,($801A)
            0x23,                   # $803B INC HL
            0xCB, 0x74,             # $803C BIT 6,H
            0x28, 0xC3,             # $803E JR Z,$8003
            0xCB, 0x4D,             # $8040 BIT 1,L
            0x28, 0xBF,             # $8042 JR Z,$8003
       )
        self._test_read_only(code, 0x8000)

    def test_rst(self):
        simulator, memory, registers = self._get_simulator([0] * 65536)
        for sp in range(1, 16386):
            for opcode, exp_pc in (
                    (0xC7, 0x00), # RST $00
                    (0xCF, 0x08), # RST $08
                    (0xD7, 0x10), # RST $10
                    (0xDF, 0x18), # RST $18
                    (0xE7, 0x20), # RST $20
                    (0xEF, 0x28), # RST $28
                    (0xF7, 0x30), # RST $30
                    (0xFF, 0x38), # RST $38
            ):
                memory[0x8000] = opcode
                registers[SP] = sp
                simulator.run(0x8000)
                self.assertEqual(registers[PC], exp_pc)
                if sp > 1:
                    self.assertEqual(memory[sp - 2], 0)
                if sp < 16385:
                    self.assertEqual(memory[sp - 1], 0)

class SimulatorTest(SkoolKitTestCase):
    def _verify(self, tracer, checksum):
        simulator = Simulator([0] * 65536, config={'c': CSimulator})
        simulator.set_tracer(tracer)
        tracer.run(simulator, CSimulator)
        self.assertEqual(tracer.checksum, checksum)

class ALOTest(SimulatorTest):
    def test_add_a_r(self):
        self._verify(AFRTracer(128), '1c6a3e0f330119a63fd3d46cda7e7acc')

    def test_add_a_a(self):
        self._verify(AFTracer(135), '8a5b656618120683ff1e8b2c91e55315')

    def test_adc_a_r(self):
        self._verify(AFRTracer(136), '0ae2d98f422d958f8ca77645a3b17aad')

    def test_adc_a_a(self):
        self._verify(AFTracer(143), 'af1966e41681c026ad6c9d6e12fc3ed8')

    def test_sub_r(self):
        self._verify(AFRTracer(144), '7b83a54cdd1c371a61ab9a643f1b435f')

    def test_sub_a(self):
        self._verify(AFTracer(151), 'f83836b3beef2cf62227b74fa2db50d5')

    def test_sbc_a_r(self):
        self._verify(AFRTracer(152), 'b4cbffcca3bdc458fd705d0b3dbcd3d9')

    def test_sbc_a_a(self):
        self._verify(AFTracer(159), '56af67d5c20e1fe7956207a4059edcc6')

    def test_and_r(self):
        self._verify(AFRTracer(160), 'a1b1b04170d249215f640d124901779a')

    def test_and_a(self):
        self._verify(AFTracer(167), '31ae45e207c05e600804ac1988828251')

    def test_xor_r(self):
        self._verify(AFRTracer(168), 'ff7501c5bc9d6ea6b2c097285e2d3d64')

    def test_xor_a(self):
        self._verify(AFTracer(175), '877412cf02e8552f3b834d8bcca0676f')

    def test_or_r(self):
        self._verify(AFRTracer(176), 'ed3bf5d700d7a756a0e458eb82f7bf05')

    def test_or_a(self):
        self._verify(AFTracer(183), '00d7b2313b6ea20857481badfa96b2a2')

    def test_cp_r(self):
        self._verify(AFRTracer(184), 'dbd26489cd3c0bb8ec4693c291b41dce')

    def test_cp_a(self):
        self._verify(AFTracer(191), '63cec365d0cfddd18244fb6025402450')

class DAATest(SimulatorTest):
    def test_daa(self):
        self._verify(AFTracer(39), '34cfcda66d6592aded581d6b96ba7362')

class SCFTest(SimulatorTest):
    def test_scf(self):
        self._verify(FTracer(55), 'c9a7fca843329542556862e58024cc72')

    def test_ccf(self):
        self._verify(FTracer(63), '1a50e83953cd4846305c4eade745d647')

class CPLTest(SimulatorTest):
    def test_cpl(self):
        self._verify(AFTracer(47), 'deb05b693f42d3ec373590cd8feea460')

class NEGTest(SimulatorTest):
    def test_neg(self):
        self._verify(AFTracer(237, 68), '70ade5872635e86f4cacbdc84fe5b724')

class RA1Test(SimulatorTest):
    def test_rlca(self):
        self._verify(AFTracer(7), '9dc646a13ac28f1f95859834feb321fe')

    def test_rrca(self):
        self._verify(AFTracer(15), 'ce72473474024199ea65180a94449845')

    def test_rla(self):
        self._verify(AFTracer(23), 'fe58ba7e2c997e99292b3c63e0346e53')

    def test_rra(self):
        self._verify(AFTracer(31), '875b8df4ff9b0be8f80c91ec6a81a37d')

class SROTest(SimulatorTest):
    def test_rlc_r(self):
        self._verify(FRTracer(203, 0), 'e512b2336da2db2924462a397db18989')

    def test_rrc_r(self):
        self._verify(FRTracer(203, 8), 'fb629c7da21d006f883f15c868de36f2')

    def test_rl_r(self):
        self._verify(FRTracer(203, 16), '94d76d52a9722dd4c4ff589d867b0ad4')

    def test_rr_r(self):
        self._verify(FRTracer(203, 24), 'e867de27d6eb893eb0b61b3be7106c07')

    def test_sla_r(self):
        self._verify(FRTracer(203, 32), 'aa0a3f81d903365ca3625adafcf8bf92')

    def test_sra_r(self):
        self._verify(FRTracer(203, 40), '7b356b838601a6dceb30292c4e301ffa')

    def test_sll_r(self):
        self._verify(FRTracer(203, 48), '90c0972cab960ba80aed1059f9867160')

    def test_srl_r(self):
        self._verify(FRTracer(203, 56), 'b4ae827e923d4a9cda244056b61ca65a')

    def test_rlc_r_r(self):
        self._verify(RSTracer(0), '1829457fc451db03fe9eafdd651b5d6b')

    def test_rrc_r_r(self):
        self._verify(RSTracer(8), 'b958b9c7332b86cbe22f01fea9a2b10f')

    def test_rl_r_r(self):
        self._verify(RSTracer(16), '76242d1e4d0b9a1b0f8741bc80844367')

    def test_rr_r_r(self):
        self._verify(RSTracer(24), '66353d9456c554be329352640feed04f')

    def test_sla_r_r(self):
        self._verify(RSTracer(32), 'd0c1118c36798b3f38817befce049383')

    def test_sra_r_r(self):
        self._verify(RSTracer(40), '90f0511e54206c36f9ad7c2349df4360')

    def test_sll_r_r(self):
        self._verify(RSTracer(48), 'f618f40e4093f49f52c6e1d70e6f4cd4')

    def test_srl_r_r(self):
        self._verify(RSTracer(56), 'ec2530a0940da922ad62680ee5cec23e')

class INCTest(SimulatorTest):
    def test_inc_r(self):
        self._verify(FRTracer(4), '486b2838e58dd05b38b607d8817c0a3e')

    def test_dec_r(self):
        self._verify(FRTracer(5), '965cf60398a9a34a32b0870ba747e65e')

class AHLTest(SimulatorTest):
    def test_add_hl_rr(self):
        self._verify(HLRRFTracer(9), '72f5c0ca1f607654448d41ba83f51c52')

    def test_adc_hl_rr(self):
        self._verify(HLRRFTracer(237, 74), '239e29da51c0bef37b131f3e0b1c731c')

    def test_sbc_hl_rr(self):
        self._verify(HLRRFTracer(237, 66), '0d97517afe1301cec29656ecd4a8d6aa')

    def test_add_hl_hl(self):
        self._verify(HLFTracer(41), 'c1e9d4ef148c912ed4d5ddbd3d761eb4')

    def test_adc_hl_hl(self):
        self._verify(HLFTracer(237, 106), '7540639ced53d305f2ebff71af813cc8')

    def test_sbc_hl_hl(self):
        self._verify(HLFTracer(237, 98), 'b2352766d380075636c4cf0a38a7e7d8')

class BLKTest(SimulatorTest):
    def test_ldi(self):
        self._verify(BlockTracer(237, 160), 'b45a630491a39fe5e60b08e8654cf885')

    def test_ldd(self):
        self._verify(BlockTracer(237, 168), '68e3af1acfad1b96383226598dc264bc')

    def test_cpi(self):
        self._verify(BlockTracer(237, 161), 'e95c3e26f058171f59c4dcf975850d5a')

    def test_cpd(self):
        self._verify(BlockTracer(237, 169), 'bbb5ec40ffa641aaeae8f94a55e7a739')

    def test_ini(self):
        self._verify(BlockTracer(237, 162), '1e0fb5b9932f4df1a2d832d9aaa8ae3e')

    def test_ind(self):
        self._verify(BlockTracer(237, 170), 'ce2f4816f1fce43c5fe5a36b9f14b4c0')

    def test_outi(self):
        self._verify(BlockTracer(237, 163), '212463fd8c672c6d2aadca3c6c047c55')

    def test_outd(self):
        self._verify(BlockTracer(237, 171), '1a944b9e160bb9232704479b70207f28')

class BITTest(SimulatorTest):
    def test_bit_n(self):
        self._verify(BitTracer(), 'ed43b8246d6f0dd377d4c1451c98d7f6')

class RRDTest(SimulatorTest):
    def test_rrd(self):
        self._verify(RRDRLDTracer(237, 103), 'd7b697dcdab00d201ac393244e9aebb2')

    def test_rld(self):
        self._verify(RRDRLDTracer(237, 111), '34620204b96b6cd1769cf1190e0c1353')

class INRTest(SimulatorTest):
    def test_in_r_c(self):
        self._verify(InTracer(), 'b04d018542b09b48e749a0dc14344e38')

class AIRTest(SimulatorTest):
    def test_ld_a_i(self):
        self._verify(AIRTracer(14, 237, 87), 'c9d853ee965280e89f31716900609e01')

    def test_ld_a_r(self):
        self._verify(AIRTracer(15, 237, 95), '0e93965958b098fc226bd46de0818383')
