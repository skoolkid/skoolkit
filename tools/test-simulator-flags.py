#!/usr/bin/env python3

import sys
import os
import unittest

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, f'{SKOOLKIT_HOME}')

from skoolkit.simulator import Simulator
from sim_test_tracers import *

REGISTERS = ('B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A')

ADD_A_r = '94d11617ef16363974532987b3d6435d'
ADD_A_A = 'b3255524a4f4496f91b72b9487e1c2f2'
ADC_A_r = '2f66412d4427588cce4ad21a6a1f80e8'
ADC_A_A = '215c4452e0a3029867ab60783fe9ce53'
SUB_r = 'fe66eed24306aef98870ab5d36b2e4f4'
SUB_A = 'd4665ee7436c8cdb18ac88d71ce1f745'
SBC_A_r = 'e73292a348f82706587d3adafb2f2bcc'
SBC_A_A = 'e4e7d5586ece48f9c8625f5c9cc2d17a'
AND_r = '6a2b0f982cad3d012db6924b5801a167'
AND_A = '153af0c2fb5636aeb7e887ff3a04d9da'
XOR_r = 'cf1542da7149725f83eba3bc0709be0b'
XOR_A = 'eb543679f6a2a9f3a2afcf22163be7f2'
OR_r = 'a9070d2d8bd3ff554c8e406096dc2bd7'
OR_A = 'a64900a4e9443713cfced1cc9e608c44'
CP_r = '6417db6acd2d6e2bdd0ba27115b4e158'
CP_A = '1fab032e90e72158e53eb5363ab99f9a'
DAA = '4312f5a5e95c582dbee61b482eee9d6b'
SCF = 'ee859b0e9650b7e36cb0ce1b73145a77'
CCF = '988c43163ba13c67aa6cd315c7018739'
CPL = 'c57876662ed32c7e9f8585ea0412a53f'
NEG = 'aadeb04c1a4f01187e4fa8dff6cc461a'
RLCA = '98b1e8bef9cba9bc6c28568572114daa'
RRCA = '1fdcb1064d373e43cb9d3d8dfd6e6d50'
RLA = '8bbfa478dc913fe70c7298c8b79812df'
RRA = '03a117d7ffeeb9055192c168c6950168'
RLC_r = '43ea1882ff46d8f2bb302d2cac821824'
RRC_r = 'd99e696ebf9ef8cdf7837c1321f489c3'
RL_r = 'e77a70aaccbee47f14cd7886469063aa'
RR_r = 'e8f1af0d8d04c67d154cc2c0245ea564'
SLA_r = 'e77a70aaccbee47f14cd7886469063aa'
SRA_r = 'fda90b011795145dd96ece00b2a12de8'
SLL_r = '13e46312e09feab46121e982cabebec4'
SRL_r = 'e8f1af0d8d04c67d154cc2c0245ea564'
INC_r = '03d99cd05b4016b7e207de3c454c4a4e'
DEC_r = 'eef164a88a4a0690653810db93737fc2'
ADD_HL_rr = '27c15637bb3f5b9db0ace1c07926de58'
ADC_HL_rr = '3dadc7ba1d95089125f02edf938edad3'
SBC_HL_rr = '2f632f9bb90d783ff508f603795c35d8'
ADD_HL_HL = '7c210f55e8572baf7faeb66fed851095'
ADC_HL_HL = 'ccd8b92bd56392081f2a94384b9956e0'
SBC_HL_HL = 'fde6fa73961772b0016d74574afc9893'
LDI = '8cace5eb645d7593094970461273a17c'
LDD = 'acb448edbe5827619b6fc4aaae615013'
CPI = '276f4bc587f5d360aec77877ccab0a56'
CPD = '809011c709cc537f68dab36aae8257b1'
INI = '7c97d8445ff734960d82a08ec0c82274'
IND = '5915d4d5a350ca4a1eb5b03666986eee'
OUTI = 'da88db329b1a92d296a7353cb7747d00'
OUTD = 'f503707ab393b36f3c97acdb7b1305e0'

class SimulatorTest(unittest.TestCase):
    def _test_instruction(self, op, tclass, targs, checksum, opcodes, snapshot=None):
        start = 32768
        if snapshot is None:
            snapshot = [0] * 65536
        if isinstance(opcodes, int):
            snapshot[start] = opcodes
        else:
            snapshot[start:start + len(opcodes)] = opcodes
        tracer = tclass(start, *targs)
        simulator = Simulator(snapshot, {'HL': 16384, 'IX': 16385, 'IY': 16386})
        simulator.add_tracer(tracer)
        simulator.run(start)
        reg = targs[-1] if targs and isinstance(targs[-1], str) else ''
        self.assertEqual(tracer.checksum, checksum, f"Checksum failure for '{op}{reg}'")

class ArithmeticLogicTest(SimulatorTest):
    def _test_alo(self, op, checksum, opcode):
        for i, reg in enumerate(('B', 'C', 'D', 'E', 'H', 'L', '(HL)')):
            self._test_instruction(op, AFRTracer, (reg,), checksum, opcode + i)

        self._test_instruction(op, AFRTracer, ('n',), checksum, opcode + 0x46)

        self._test_instruction(op, AFRTracer, ('IXh',), checksum, (0xDD, opcode + 0x04))
        self._test_instruction(op, AFRTracer, ('IYh',), checksum, (0xFD, opcode + 0x04))

        self._test_instruction(op, AFRTracer, ('IXl',), checksum, (0xDD, opcode + 0x05))
        self._test_instruction(op, AFRTracer, ('IYl',), checksum, (0xFD, opcode + 0x05))

        self._test_instruction(op, AFRTracer, ('(IX+d)',), checksum, (0xDD, opcode + 0x06))
        self._test_instruction(op, AFRTracer, ('(IY+d)',), checksum, (0xFD, opcode + 0x06))

    def test_add_a_r(self):
        self._test_alo('ADD A,', ADD_A_r, 0x80)

    def test_add_a_a(self):
        self._test_instruction('ADD A,A', AFTracer, (), ADD_A_A, 0x87)

    def test_adc_a_r(self):
        self._test_alo('ADC A,', ADC_A_r, 0x88)

    def test_adc_a_a(self):
        self._test_instruction('ADC A,A', AFTracer, (), ADC_A_A, 0x8F)

    def test_sub_r(self):
        self._test_alo('SUB ', SUB_r, 0x90)

    def test_sub_a(self):
        self._test_instruction('SUB A', AFTracer, (), SUB_A, 0x97)

    def test_sbc_a_r(self):
        self._test_alo('SBC A,', SBC_A_r, 0x98)

    def test_sbc_a_a(self):
        self._test_instruction('SBC A,A', AFTracer, (), SBC_A_A, 0x9F)

    def test_and_r(self):
        self._test_alo('AND ', AND_r, 0xA0)

    def test_and_a(self):
        self._test_instruction('AND A', AFTracer, (), AND_A, 0xA7)

    def test_xor_r(self):
        self._test_alo('XOR ', XOR_r, 0xA8)

    def test_xor_a(self):
        self._test_instruction('XOR A', AFTracer, (), XOR_A, 0xAF)

    def test_or_r(self):
        self._test_alo('OR ', OR_r, 0xB0)

    def test_or_a(self):
        self._test_instruction('OR A', AFTracer, (), OR_A, 0xB7)

    def test_cp_r(self):
        self._test_alo('CP ', CP_r, 0xB8)

    def test_cp_a(self):
        self._test_instruction('CP A', AFTracer, (), CP_A, 0xBF)

class AccumulatorTest(SimulatorTest):
    def test_daa(self):
        self._test_instruction('DAA', DAATracer, (), DAA, 0x27)

    def test_cpl(self):
        self._test_instruction('CPL', AFTracer, (0xFF,), CPL, 0x2F)

    def test_neg(self):
        for opcode in (0x44, 0x4C, 0x54, 0x5C, 0x64, 0x6C, 0x74, 0x7C):
            self._test_instruction('NEG', AFTracer, (0xFF,), NEG, (0xED, opcode))

class CarryFlagTest(SimulatorTest):
    def test_scf(self):
        self._test_instruction('SCF', FTracer, (), SCF, 0x37)

    def test_ccf(self):
        self._test_instruction('CCF', FTracer, (), CCF, 0x3F)

class ShiftRotateTest(SimulatorTest):
    def _test_sro(self, op, checksum, opcode):
        for i, reg in enumerate(('B', 'C', 'D', 'E', 'H', 'L', '(HL)', 'A')):
            self._test_instruction(op, FRTracer, (reg,), checksum, (0xCB, opcode + i))

        self._test_instruction(op, FRTracer, ('(IX+d)',), checksum, (0xDD, 0xCB, 0, opcode + 0x06))
        self._test_instruction(op, FRTracer, ('(IY+d)',), checksum, (0xFD, 0xCB, 0, opcode + 0x06))

    def test_rlca(self):
        self._test_instruction('RLCA', AFTracer, (0xFFFF,), RLCA, 0x07)

    def test_rrca(self):
        self._test_instruction('RRCA', AFTracer, (0xFFFF,), RRCA, 0x0F)

    def test_rla(self):
        self._test_instruction('RLA', AFTracer, (0xFFFF,), RLA, 0x17)

    def test_rra(self):
        self._test_instruction('RRA', AFTracer, (0xFFFF,), RRA, 0x1F)

    def test_rlc_r(self):
        self._test_sro('RLC ', RLC_r, 0x00)

    def test_rrc_r(self):
        self._test_sro('RRC ', RRC_r, 0x08)

    def test_rl_r(self):
        self._test_sro('RL ', RL_r, 0x10)

    def test_rr_r(self):
        self._test_sro('RR ', RR_r, 0x18)

    def test_sla_r(self):
        self._test_sro('SLA ', SLA_r, 0x20)

    def test_sra_r(self):
        self._test_sro('SRA ', SRA_r, 0x28)

    def test_sll_r(self):
        self._test_sro('SLL ', SLL_r, 0x30)

    def test_srl_r(self):
        self._test_sro('SRL ', SRL_r, 0x38)

class IncDec8Test(SimulatorTest):
    def _test_inc_dec(self, op, checksum, opcode):
        for i, reg in enumerate(('B', 'C', 'D', 'E', 'H', 'L', '(HL)')):
            self._test_instruction(op, FRTracer, (reg,), checksum, opcode + 8 * i)

        self._test_instruction(op, FRTracer, ('IXh',), checksum, (0xDD, opcode + 0x20))
        self._test_instruction(op, FRTracer, ('IYh',), checksum, (0xFD, opcode + 0x20))

        self._test_instruction(op, FRTracer, ('IXl',), checksum, (0xDD, opcode + 0x28))
        self._test_instruction(op, FRTracer, ('IYl',), checksum, (0xFD, opcode + 0x28))

        self._test_instruction(op, FRTracer, ('(IX+d)',), checksum, (0xDD, opcode + 0x30))
        self._test_instruction(op, FRTracer, ('(IY+d)',), checksum, (0xFD, opcode + 0x30))

    def test_inc_r(self):
        self._test_inc_dec('INC ', INC_r, 0x04)

    def test_dec_r(self):
        self._test_inc_dec('DEC ', DEC_r, 0x05)

class Arithmetic16Test(SimulatorTest):
    def _test_hl_rr_arithmetic(self, op, checksum, opcodes):
        for i, reg in enumerate(('BC', 'DE', 'HL', 'SP')):
            if reg != 'HL':
                codes = list(opcodes)
                codes[-1] += 16 * i
                self._test_instruction(op + ' HL,', HLRRFTracer, ('HL', reg), checksum, codes)
                if op == 'ADD':
                    self._test_instruction('ADD IX,', HLRRFTracer, (('IXh', 'IXl'), reg), checksum, [0xDD] + codes)
                    self._test_instruction('ADD IY,', HLRRFTracer, (('IYh', 'IYl'), reg), checksum, [0xFD] + codes)

    def _test_hl_hl_arithmetic(self, op, checksum, opcodes):
        self._test_instruction(op + ' HL,', HLFTracer, ('HL',), checksum, opcodes)
        if op == 'ADD':
            self._test_instruction('ADD IX,IX', HLFTracer, (('IXh', 'IXl'),), checksum, (0xDD,) + opcodes)
            self._test_instruction('ADD IY,IY', HLFTracer, (('IYh', 'IYl'),), checksum, (0xFD,) + opcodes)

    def test_add_hl_rr(self):
        self._test_hl_rr_arithmetic('ADD', ADD_HL_rr, (0x09,))

    def test_adc_hl_rr(self):
        self._test_hl_rr_arithmetic('ADC', ADC_HL_rr, (0xED, 0x4A))

    def test_sbc_hl_rr(self):
        self._test_hl_rr_arithmetic('SBC', SBC_HL_rr, (0xED, 0x42))

    def test_add_hl_hl(self):
        self._test_hl_hl_arithmetic('ADD', ADD_HL_HL, (0x29,))

    def test_adc_hl_hl(self):
        self._test_hl_hl_arithmetic('ADC', ADC_HL_HL, (0xED, 0x6A))

    def test_sbc_hl_hl(self):
        self._test_hl_hl_arithmetic('SBC', SBC_HL_HL, (0xED, 0x62))

class BlockTest(SimulatorTest):
    def test_ldi(self):
        self._test_instruction('LDI', BlockTracer, (), LDI, (0xED, 0xA0))

    def test_ldd(self):
        self._test_instruction('LDD', BlockTracer, (), LDD, (0xED, 0xA8))

    def test_ldir(self):
        self._test_instruction('LDIR', BlockTracer, (), LDI, (0xED, 0xB0))

    def test_lddr(self):
        self._test_instruction('LDDR', BlockTracer, (), LDD, (0xED, 0xB8))

    def test_cpi(self):
        self._test_instruction('CPI', BlockTracer, (), CPI, (0xED, 0xA1))

    def test_cpd(self):
        self._test_instruction('CPD', BlockTracer, (), CPD, (0xED, 0xA9))

    def test_cpir(self):
        self._test_instruction('CPIR', BlockTracer, (), CPI, (0xED, 0xB1))

    def test_cpdr(self):
        self._test_instruction('CPDR', BlockTracer, (), CPD, (0xED, 0xB9))

    def test_ini(self):
        self._test_instruction('INI', BlockTracer, (), INI, (0xED, 0xA2))

    def test_ind(self):
        self._test_instruction('IND', BlockTracer, (), IND, (0xED, 0xAA))

    def test_inir(self):
        self._test_instruction('INIR', BlockTracer, (), INI, (0xED, 0xB2))

    def test_indr(self):
        self._test_instruction('INDR', BlockTracer, (), IND, (0xED, 0xBA))

    def test_outi(self):
        self._test_instruction('OUTI', BlockTracer, (), OUTI, (0xED, 0xA3))

    def test_outd(self):
        self._test_instruction('OUTD', BlockTracer, (), OUTD, (0xED, 0xAB))

    def test_otir(self):
        self._test_instruction('OTIR', BlockTracer, (), OUTI, (0xED, 0xB3))

    def test_otdr(self):
        self._test_instruction('OTDR', BlockTracer, (), OUTD, (0xED, 0xBB))

if __name__ == '__main__':
    unittest.main()
