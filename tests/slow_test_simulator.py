from skoolkittest import SkoolKitTestCase
from skoolkit.simulator import Simulator
from sim_test_tracers import *

class SimulatorTest(SkoolKitTestCase):
    def _verify(self, tracer, checksum):
        simulator = Simulator([0] * 65536)
        simulator.set_tracer(tracer)
        simulator.run(0)
        self.assertEqual(tracer.checksum, checksum)

    def test_add_a_r(self):
        self._verify(AFRTracer(128), '9afe277de639b935fafc8456f013f0fa')

    def test_add_a_a(self):
        self._verify(AFTracer(135), 'fb0d4abb4e8d4fd5cfaa217e779cf1a9')

    def test_adc_a_r(self):
        self._verify(AFRTracer(136), '7d8c3924ba5f4360d4702220d6a7494e')

    def test_adc_a_a(self):
        self._verify(AFTracer(143), 'cdef42fc2700d32acfe9d386b1f86aea')

    def test_sub_r(self):
        self._verify(AFRTracer(144), '9651ec05fc16873d052628e38ba8784c')

    def test_sub_a(self):
        self._verify(AFTracer(151), 'e2005356ced7923690fe5ba5d8c6e5b2')

    def test_sbc_a_r(self):
        self._verify(AFRTracer(152), '82a5257808fa94703d31ae0d8ba24f7a')

    def test_sbc_a_a(self):
        self._verify(AFTracer(159), '678056ef932c11bdb44bcd39dcbb8f96')

    def test_and_r(self):
        self._verify(AFRTracer(160), 'a156f5c67aa471927729eb6f13ed638d')

    def test_and_a(self):
        self._verify(AFTracer(167), '5656eedf422c04e36dfbcabec442692c')

    def test_xor_r(self):
        self._verify(AFRTracer(168), 'ecc5b48b7cc84554a86b60d8af7ebdfd')

    def test_xor_a(self):
        self._verify(AFTracer(175), 'c18cd8dc96f251903d73f7d9757a3bad')

    def test_or_r(self):
        self._verify(AFRTracer(176), 'fb6c40cc1d5aeeacaab30cd5f5f6f2fd')

    def test_or_a(self):
        self._verify(AFTracer(183), '7b9198ee6e11ccac257a7d4a3a4b1b5d')

    def test_cp_r(self):
        self._verify(AFRTracer(184), '4a4c413096de68d3043aa6ca5efa306d')

    def test_cp_a(self):
        self._verify(AFTracer(191), '48d5726805ab6c108d0ad438cc751973')

    def test_daa(self):
        self._verify(AFTracer(39), '03fcf0038e8955cbf04a89b6550b7aa9')

    def test_scf(self):
        self._verify(FTracer(55), '999ed20ae7df47a0845b24601debc892')

    def test_ccf(self):
        self._verify(FTracer(63), '5cce98362580dde26e01ee7754446f44')

    def test_cpl(self):
        self._verify(AFTracer(47), '4e3833af3b4d1f825f79dfde637eb1df')

    def test_neg(self):
        self._verify(AFTracer(237, 68), 'ca3142ddbdfb60939eb40895f4a9939a')

    def test_rlca(self):
        self._verify(AFTracer(7), '0bb7a194ef2060d1a2429960d42ea82f')

    def test_rrca(self):
        self._verify(AFTracer(15), 'bc463c5bf52c8e4869ffa5de70a98d54')

    def test_rla(self):
        self._verify(AFTracer(23), 'ecc970ff4a83fa0c0cb6d3586c51d1a9')

    def test_rra(self):
        self._verify(AFTracer(31), '7128349be359517011763e7ba0c5ab8a')

    def test_rlc_r(self):
        self._verify(FRTracer(203, 0), 'ed721840662b861550518f47c34e2f8c')

    def test_rrc_r(self):
        self._verify(FRTracer(203, 8), 'e8ca7ba9842929f844629cec3c89714c')

    def test_rl_r(self):
        self._verify(FRTracer(203, 16), 'cebcb2448feff02bb62d8e7d32704033')

    def test_rr_r(self):
        self._verify(FRTracer(203, 24), '81f5b727dd6696fc0252f2c1a364c555')

    def test_sla_r(self):
        self._verify(FRTracer(203, 32), 'c1cd09dd822fc913755500249d5b73a8')

    def test_sra_r(self):
        self._verify(FRTracer(203, 40), '3978ac5e0144aa42fbac81fa47a28a84')

    def test_sll_r(self):
        self._verify(FRTracer(203, 48), '5b39f7612ffe24d044c823d966458b31')

    def test_srl_r(self):
        self._verify(FRTracer(203, 56), '50dbb30b14a062ec0dcebc38013943cc')

    def test_inc_r(self):
        self._verify(FRTracer(4), '6f0fd59747a860949c9498ac41870aad')

    def test_dec_r(self):
        self._verify(FRTracer(5), 'e5d2a987c2c21a7af1648c9721fd964d')

    def test_add_hl_rr(self):
        self._verify(HLRRFTracer(9), '789049808da2dfdc794dfb9fa1f1df83')

    def test_adc_hl_rr(self):
        self._verify(HLRRFTracer(237, 74), '12622bf85fac94ed4d11839aff1b6090')

    def test_sbc_hl_rr(self):
        self._verify(HLRRFTracer(237, 66), 'b109b2492f87adf7af7b9a60996e952b')

    def test_add_hl_hl(self):
        self._verify(HLFTracer(41), '0f48f19bc496bb25260a105233dd5337')

    def test_adc_hl_hl(self):
        self._verify(HLFTracer(237, 106), '69eded5109a49624aa9f3896698cfa83')

    def test_sbc_hl_hl(self):
        self._verify(HLFTracer(237, 98), '6af47f849e6857614c0f736e9751f4f5')

    def test_ldi(self):
        self._verify(BlockTracer(237, 160), 'b2f9ffbc4ad978abb609b521350bbf4f')

    def test_ldd(self):
        self._verify(BlockTracer(237, 168), '79c3cf9c6028a4804b148677b55ca7b9')

    def test_cpi(self):
        self._verify(BlockTracer(237, 161), '3b507013d9c139ccacda1b13e2f5233d')

    def test_cpd(self):
        self._verify(BlockTracer(237, 169), 'df68d8c41fa163541f9c578e3a5088cb')

    def test_ini(self):
        self._verify(BlockTracer(237, 162), 'c746797f505ef6d76d584a14e7be5f52')

    def test_ind(self):
        self._verify(BlockTracer(237, 170), '842d359bf8fd0992ec8d90e63da5d185')

    def test_outi(self):
        self._verify(BlockTracer(237, 163), '8f7159ef1b315e0dcdee92f1d2cd97af')

    def test_outd(self):
        self._verify(BlockTracer(237, 171), 'ee2bace497c622d99df91a244ad70927')

    def test_bit_n(self):
        self._verify(BitTracer(), 'e91bf78daa2180817191118dc7866d1c')

    def test_rrd(self):
        self._verify(RRDRLDTracer(237, 103), 'ca24ee139a7fb9697430ce9da6f79339')

    def test_rld(self):
        self._verify(RRDRLDTracer(237, 111), 'db8f7db66851400ac3f4ad8529bbdb76')

    def test_in_r_c(self):
        self._verify(InTracer(), '7ba7b0c55c35f3b58c43ab54ba2b5e55')

    def test_ld_a_i(self):
        self._verify(AIRTracer(14, 237, 87), 'a6c889a130646c2679af05630cb9a025')

    def test_ld_a_r(self):
        self._verify(AIRTracer(15, 237, 95), 'b78188cd26bbb72249135204af535c43')
