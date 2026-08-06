import array

from skoolkittest import SkoolKitTestCase

from skoolkit import CSimulator
from skoolkit.loadsample import ACCELERATORS, Accelerator
from skoolkit.pagingtracer import Memory

class InvalidMemory48K:
    def __len__(self):
        return 0x10000

class TestLoadTracer:
    def __init__(self):
        self.border = [(0, 1)]
        self.edges = array.array('Q', (0, 1))
        self.in_min_addr = 0
        self.state = array.array('Q', (0, 1))
        self.fast_load = lambda: None
        self.list_accelerators = False
        self.accel_dec_a = 1
        self.accelerators = set(Accelerator(*ACCELERATORS[a]) for a in ('activision', 'alkatraz'))
        self.stop = 0

class TestKeypressTracer:
    def __init__(self):
        self.border = [(0, 1)]

class TestKeyboardTracer:
    def __init__(self):
        self.border = [(0, 1)]
        self.keys = ['0']

class TestTracer:
    pass

class CSimulatorAPITest(SkoolKitTestCase):
    def setUp(self):
        super().setUp()
        self.assertIsNotNone(CSimulator)

    def remove_attribute(self, tcls, name, key=None):
        tracer = tcls()
        obj = key(tracer) if key else tracer
        delattr(obj, name)
        otype = type(obj).__name__
        s = CSimulator([0] * 65536)
        s.set_tracer(tracer)
        return s, f"'{otype}' object has no attribute '{name}'"

class InitTest(CSimulatorAPITest):
    def test_too_few_args(self):
        with self.assertRaises(TypeError) as cm:
            CSimulator()
        self.assertEqual(cm.exception.args[0], "function missing required argument 'memory' (pos 1)")

    def test_too_many_args(self):
        with self.assertRaises(TypeError) as cm:
            CSimulator(None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 4 arguments (5 given)")

    def test_unexpected_arg(self):
        with self.assertRaises(TypeError) as cm:
            CSimulator([0] * 65536, foo=1)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'foo'")

    def test_invalid_memory_length(self):
        with self.assertRaises(TypeError) as cm:
            CSimulator([0])
        self.assertEqual(cm.exception.args[0], "Simulator memory length is neither 65536 nor 131072")

    def test_invalid_memory_object_48k(self):
        with self.assertRaises(TypeError) as cm:
            CSimulator(InvalidMemory48K())
        self.assertEqual(cm.exception.args[0], "Failed to create iterator for memory")

    def test_no_roms(self):
        m = Memory()
        delattr(m, 'roms')
        with self.assertRaises(AttributeError) as cm:
            CSimulator(m)
        self.assertEqual(cm.exception.args[0], "'Memory' object has no attribute 'roms'")

    def test_invalid_roms(self):
        m = Memory()
        m.roms = (bytes([0] * 16384),) * 3
        with self.assertRaises(TypeError) as cm:
            CSimulator(m)
        self.assertEqual(cm.exception.args[0], "Simulator memory.roms is not a 2-element tuple")

    def test_no_banks(self):
        m = Memory()
        delattr(m, 'banks')
        with self.assertRaises(AttributeError) as cm:
            CSimulator(m)
        self.assertEqual(cm.exception.args[0], "'Memory' object has no attribute 'banks'")

    def test_invalid_banks(self):
        m = Memory()
        m.banks = [[0]] * 7
        with self.assertRaises(TypeError) as cm:
            CSimulator(m)
        self.assertEqual(cm.exception.args[0], "Simulator memory.banks is not an 8-element list")

    def test_no_o7ffd(self):
        m = Memory()
        delattr(m, 'o7ffd')
        with self.assertRaises(AttributeError) as cm:
            CSimulator(m)
        self.assertEqual(cm.exception.args[0], "'Memory' object has no attribute 'o7ffd'")

    def test_invalid_byte_value(self):
        m = [0] * 65536
        m[23456] = None
        with self.assertRaises(TypeError) as cm:
            CSimulator(m)
        self.assertEqual(cm.exception.args[0], "Object at memory address 23456 is not an integer")

class AttributesTest(CSimulatorAPITest):
    def test_memory_48k(self):
        memory = [n & 0xFF for n in range(65536)]
        s = CSimulator(memory)
        self.assertTrue(hasattr(s, 'memory'))
        self.assertEqual(len(s.memory), len(memory))
        self.assertTrue(all(b1 == b2 for b1, b2 in zip(memory, s.memory)))

    def test_registers(self):
        s = CSimulator([0] * 65536, {'A': 123})
        self.assertTrue(hasattr(s, 'registers'))
        self.assertEqual(len(s.registers), 30)
        self.assertEqual(s.registers[0], 123)

    def test_tracer(self):
        s = CSimulator([0] * 65536)
        t = TestTracer()
        self.assertFalse(hasattr(s, 'tracer'))
        s.set_tracer(t)
        self.assertTrue(hasattr(s, 'tracer'))
        self.assertIs(s.tracer, t)

    def test_frame_duration(self):
        s = CSimulator([0] * 65536, config={'frame_duration': 12345})
        self.assertTrue(hasattr(s, 'frame_duration'))
        self.assertEqual(s.frame_duration, 12345)

class LoadTest(CSimulatorAPITest):
    def _test_missing_attribute(self, tcls, name, key=None):
        s, exp_error = self.remove_attribute(tcls, name, key)
        with self.assertRaises(AttributeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.load(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 7 positional arguments (1 given)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.load(1, True, False, 100, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 7 arguments (8 given)")

    def test_invalid_stop(self):
        t = TestLoadTracer()
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        stop = {}
        with self.assertRaises(TypeError) as cm:
            s.load(stop, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'dict' object cannot be interpreted as an integer")

    def test_invalid_fast_load(self):
        t = TestLoadTracer()
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        fast_load = None
        with self.assertRaises(TypeError) as cm:
            s.load(1, fast_load, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_invalid_finish_tape(self):
        t = TestLoadTracer()
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        finish_tape = 'no'
        with self.assertRaises(TypeError) as cm:
            s.load(1, 1, finish_tape, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'str' object cannot be interpreted as an integer")

    def test_invalid_timeout(self):
        t = TestLoadTracer()
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        timeout = ()
        with self.assertRaises(TypeError) as cm:
            s.load(1, 1, 1, timeout, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 4 must be int, not tuple")

    def test_no_tracer(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.load(1, True, False, 100, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_no_border(self):
        self._test_missing_attribute(TestLoadTracer, 'border')

    def test_no_edges(self):
        self._test_missing_attribute(TestLoadTracer, 'edges')

    def test_edges_unbufferable(self):
        t = TestLoadTracer()
        t.edges = [0, 1]
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "a bytes-like object is required, not 'list'")

    def test_no_in_min_addr(self):
        self._test_missing_attribute(TestLoadTracer, 'in_min_addr')

    def test_no_state(self):
        self._test_missing_attribute(TestLoadTracer, 'state')

    def test_state_unbufferable(self):
        t = TestLoadTracer()
        t.state = [0, 1]
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "a bytes-like object is required, not 'list'")

    def test_no_fast_load(self):
        self._test_missing_attribute(TestLoadTracer, 'fast_load')

    def test_no_list_accelerators(self):
        self._test_missing_attribute(TestLoadTracer, 'list_accelerators')

    def test_no_accel_dec_a(self):
        self._test_missing_attribute(TestLoadTracer, 'accel_dec_a')

    def test_accel_dec_a_not_a_number(self):
        t = TestLoadTracer()
        t.accel_dec_a = []
        s = CSimulator([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'list' object cannot be interpreted as an integer")

    def test_no_accelerators(self):
        self._test_missing_attribute(TestLoadTracer, 'accelerators')

    def test_accelerator_no_name(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'name', key)

    def test_accelerator_no_code(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'code', key)

    def test_accelerator_no_c0(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'c0', key)

    def test_accelerator_no_c1(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'c1', key)

    def test_accelerator_no_counter(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'counter', key)

    def test_accelerator_no_inc(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'inc', key)

    def test_accelerator_no_loop_time(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'loop_time', key)

    def test_accelerator_no_loop_r_inc(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'loop_r_inc', key)

    def test_accelerator_no_ear(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'ear', key)

    def test_accelerator_no_ear_mask(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'ear_mask', key)

    def test_accelerator_no_polarity(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'polarity', key)

class PressTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 5 positional arguments (1 given)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press(None, 1, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 5 arguments (6 given)")

    def test_invalid_timeout(self):
        s = CSimulator([0] * 65536)
        s.set_tracer(TestKeypressTracer())
        timeout = []
        with self.assertRaises(TypeError) as cm:
            s.press(None, timeout, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 2 must be int, not list")

    def test_no_tracer(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.press(None, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_no_border(self):
        s, exp_error = self.remove_attribute(TestKeypressTracer, 'border')
        with self.assertRaises(AttributeError) as cm:
            s.press(None, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], exp_error)

class PressKeysTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 6 positional arguments (1 given)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None, 1, 1, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 6 arguments (7 given)")

    def test_invalid_stop(self):
        s = CSimulator([0] * 65536)
        stop = None
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None, stop, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_invalid_timeout(self):
        s = CSimulator([0] * 65536)
        timeout = set()
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None, 1, timeout, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 3 must be int, not set")

    def test_no_tracer(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.press_keys(None, 1, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_no_border(self):
        s, exp_error = self.remove_attribute(TestKeyboardTracer, 'border')
        with self.assertRaises(AttributeError) as cm:
            s.press_keys(None, 1, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_keys_no_pop(self):
        s = CSimulator([0] * 65536)
        t = TestKeyboardTracer()
        s.set_tracer(t)
        t.keys = ('1', '2')
        with self.assertRaises(AttributeError) as cm:
            s.press_keys(t.keys, 1, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'tuple' object has no attribute 'pop'")

class TraceTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.trace(1)
        self.assertEqual(cm.exception.args[0], "function takes exactly 10 positional arguments (1 given)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, 1, 1, True, None, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 10 arguments (11 given)")

    def test_no_tracer(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.trace(1, 1, 1, 1, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_invalid_max_operations(self):
        s = CSimulator([0] * 65536)
        max_operations = None
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, max_operations, 1, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 3 must be int, not None")

    def test_invalid_max_time(self):
        s = CSimulator([0] * 65536)
        max_time = ()
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, 1, max_time, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 4 must be int, not tuple")

    def test_no_border(self):
        s = CSimulator([0] * 65536)
        s.set_tracer(TestTracer())
        with self.assertRaises(AttributeError) as cm:
            s.trace(1, 1, 1, 1, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "'TestTracer' object has no attribute 'border'")

class RunTest(CSimulatorAPITest):
    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(1, 1, True, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_unexpected_arg(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(foo=1)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'foo'")

    def test_invalid_start(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_invalid_stop(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(stop=[])
        self.assertEqual(cm.exception.args[0], "'list' object cannot be interpreted as an integer")

class ExecFrameTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame()
        self.assertEqual(cm.exception.args[0], "function missing required argument 'fetch_count' (pos 1)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame(1, set(), None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_unexpected_arg(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame(1, bar=1)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'bar'")

    def test_invalid_fetch_count(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame('1')
        self.assertEqual(cm.exception.args[0], "'str' object cannot be interpreted as an integer")

class AcceptInterruptTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.accept_interrupt(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 3 positional arguments (1 given)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.accept_interrupt(None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_invalid_prev_pc(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.accept_interrupt(None, None, {})
        self.assertEqual(cm.exception.args[0], "'dict' object cannot be interpreted as an integer")

class ExecWithCBTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_with_cb(1)
        self.assertEqual(cm.exception.args[0], "function missing required argument 'rst16_cb' (pos 2)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_with_cb(1, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 2 arguments (3 given)")

    def test_invalid_stop(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_with_cb([], None)
        self.assertEqual(cm.exception.args[0], "'list' object cannot be interpreted as an integer")

class SetTracerTest(CSimulatorAPITest):
    def test_too_few_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer()
        self.assertEqual(cm.exception.args[0], "function takes at least 1 positional argument (0 given)")

    def test_too_many_args(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, 1, 1, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_unexpected_arg(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, baz=2)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'baz'")

    def test_invalid_in_r_c(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_invalid_ini(self):
        s = CSimulator([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, True, set())
        self.assertEqual(cm.exception.args[0], "'set' object cannot be interpreted as an integer")
