from skoolkittest import SkoolKitTestCase
from skoolkit.simulator import Simulator
from sim_test_tracers import *

class SimulatorTest(SkoolKitTestCase):
    def _verify(self, tracer, checksum):
        simulator = Simulator([0] * 65536)
        simulator.set_tracer(tracer)
        tracer.run(simulator)
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
        self._verify(HLRRFTracer(9), '150d6938ab4b36a65d444db86ed63126')

    def test_adc_hl_rr(self):
        self._verify(HLRRFTracer(237, 74), '9643a4192ab8ed90466640564c821614')

    def test_sbc_hl_rr(self):
        self._verify(HLRRFTracer(237, 66), '6ee65de993e5650288da7ee1e0ad749d')

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
        self._verify(AIRTracer(15, 237, 95), '8f138736f29f3976d903f654bb65dfdf')
