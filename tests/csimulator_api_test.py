import array
from collections import deque

from skoolkittest import SkoolKitTestCase

from skoolkit import CSimulator, CCMIOSimulator
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
        self.state = array.array('Q', range(10))
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

class CSimulatorAPITestBase(SkoolKitTestCase):
    def setUp(self):
        super().setUp()
        self.assertIsNotNone(self.simulator_cls)

    def remove_attribute(self, tcls, name, key=None):
        tracer = tcls()
        obj = key(tracer) if key else tracer
        delattr(obj, name)
        otype = type(obj).__name__
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(tracer)
        return s, f"'{otype}' object has no attribute '{name}'"

class InitTest:
    def test_init_too_few_args(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls()
        self.assertEqual(cm.exception.args[0], "function missing required argument 'memory' (pos 1)")

    def test_init_too_many_args(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls(None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 4 arguments (5 given)")

    def test_init_unexpected_arg(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0] * 65536, foo=1)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'foo'")

    def test_init_invalid_memory_length(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0])
        self.assertEqual(cm.exception.args[0], "Simulator memory length is neither 65536 nor 131072")

    def test_init_invalid_memory_object_48k(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls(InvalidMemory48K())
        self.assertEqual(cm.exception.args[0], "Failed to create iterator for memory")

    def test_init_no_roms(self):
        m = Memory()
        delattr(m, 'roms')
        with self.assertRaises(AttributeError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "'Memory' object has no attribute 'roms'")

    def test_init_invalid_roms(self):
        m = Memory()
        m.roms = (bytes([0] * 16384),) * 3
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "Simulator memory.roms is not a 2-element tuple")

    def test_init_rom_wrong_size(self):
        m = Memory()
        m.roms = (bytes([0] * 16383),) * 2
        with self.assertRaises(ValueError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "Memory bank size is 16383 (expected 16384)")

    def test_init_no_banks(self):
        m = Memory()
        delattr(m, 'banks')
        with self.assertRaises(AttributeError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "'Memory' object has no attribute 'banks'")

    def test_init_invalid_banks(self):
        m = Memory()
        m.banks = [[0]] * 7
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "Simulator memory.banks is not an 8-element list")

    def test_init_bank_wrong_size(self):
        m = Memory()
        m.banks = ([0] * 16383,) + m.banks[1:]
        with self.assertRaises(ValueError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "Memory bank size is 16383 (expected 16384)")

    def test_init_no_o7ffd(self):
        m = Memory()
        delattr(m, 'o7ffd')
        with self.assertRaises(AttributeError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "'Memory' object has no attribute 'o7ffd'")

    def test_init_invalid_byte_value(self):
        m = [0] * 65536
        m[23456] = None
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "Object at memory address 23456 is not an integer")

    def test_init_out_of_range_byte_value(self):
        m = [0] * 65536
        m[23456] = 2**64
        with self.assertRaises(OverflowError) as cm:
            self.simulator_cls(m)
        self.assertEqual(cm.exception.args[0], "Python int too large to convert to C long")

    def test_init_config_not_a_dict(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0] * 65536, config=[])
        self.assertEqual(cm.exception.args[0], "'config' must be a dict")

    def test_init_config_with_non_string_key(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0] * 65536, config={1: 2})
        self.assertEqual(cm.exception.args[0], "keys of 'config' must be strings")

    def test_init_frame_duration_not_an_int(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0] * 65536, config={'frame_duration': '69888'})
        self.assertEqual(cm.exception.args[0], "value of 'frame_duration' must be an integer")

    def test_init_int_active_not_an_int(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0] * 65536, config={'int_active': '32'})
        self.assertEqual(cm.exception.args[0], "value of 'int_active' must be an integer")

    def test_init_register_value_not_an_int(self):
        with self.assertRaises(TypeError) as cm:
            self.simulator_cls([0] * 65536, {'A': '1'})
        self.assertEqual(cm.exception.args[0], "unsupported operand type(s) for &: 'str' and 'int'")

class AttributesTest:
    def test_attributes_memory_48k(self):
        memory = [n & 0xFF for n in range(65536)]
        s = self.simulator_cls(memory)
        self.assertTrue(hasattr(s, 'memory'))
        self.assertEqual(len(s.memory), len(memory))
        self.assertTrue(all(b1 == b2 for b1, b2 in zip(memory, s.memory)))

    def test_attributes_registers(self):
        s = self.simulator_cls([0] * 65536, {'A': 123})
        self.assertTrue(hasattr(s, 'registers'))
        self.assertEqual(len(s.registers), 30)
        self.assertEqual(s.registers[0], 123)

    def test_attributes_tracer(self):
        s = self.simulator_cls([0] * 65536)
        t = TestTracer()
        self.assertFalse(hasattr(s, 'tracer'))
        s.set_tracer(t)
        self.assertTrue(hasattr(s, 'tracer'))
        self.assertIs(s.tracer, t)

    def test_attributes_frame_duration(self):
        s = self.simulator_cls([0] * 65536, config={'frame_duration': 12345})
        self.assertTrue(hasattr(s, 'frame_duration'))
        self.assertEqual(s.frame_duration, 12345)

class LoadTestBase:
    def _test_missing_attribute(self, tcls, name, key=None):
        s, exp_error = self.remove_attribute(tcls, name, key)
        with self.assertRaises(AttributeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_load_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.load(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 7 positional arguments (1 given)")

    def test_load_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.load(1, True, False, 100, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 7 arguments (8 given)")

    def test_load_invalid_stop(self):
        t = TestLoadTracer()
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        stop = {}
        with self.assertRaises(TypeError) as cm:
            s.load(stop, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'dict' object cannot be interpreted as an integer")

    def test_load_invalid_fast_load(self):
        t = TestLoadTracer()
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        fast_load = None
        with self.assertRaises(TypeError) as cm:
            s.load(1, fast_load, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_load_invalid_finish_tape(self):
        t = TestLoadTracer()
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        finish_tape = 'no'
        with self.assertRaises(TypeError) as cm:
            s.load(1, 1, finish_tape, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'str' object cannot be interpreted as an integer")

    def test_load_invalid_timeout(self):
        t = TestLoadTracer()
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        timeout = ()
        with self.assertRaises(TypeError) as cm:
            s.load(1, 1, 1, timeout, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 4 must be int, not tuple")

    def test_load_no_tracer(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.load(1, True, False, 100, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_load_no_border(self):
        self._test_missing_attribute(TestLoadTracer, 'border')

    def test_load_no_edges(self):
        self._test_missing_attribute(TestLoadTracer, 'edges')

    def test_load_edges_unbufferable(self):
        t = TestLoadTracer()
        t.edges = [0, 1]
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "a bytes-like object is required, not 'list'")

    def test_load_no_in_min_addr(self):
        self._test_missing_attribute(TestLoadTracer, 'in_min_addr')

    def test_load_in_min_addr_not_an_int(self):
        t = TestLoadTracer()
        t.in_min_addr = '0'
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'str' object cannot be interpreted as an integer")

    def test_load_no_state(self):
        self._test_missing_attribute(TestLoadTracer, 'state')

    def test_load_state_unbufferable(self):
        t = TestLoadTracer()
        t.state = [0, 1]
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "a bytes-like object is required, not 'list'")

    def test_load_no_fast_load(self):
        self._test_missing_attribute(TestLoadTracer, 'fast_load')

class LoadTest(LoadTestBase):
    def test_load_no_list_accelerators(self):
        self._test_missing_attribute(TestLoadTracer, 'list_accelerators')

    def test_load_no_accel_dec_a(self):
        self._test_missing_attribute(TestLoadTracer, 'accel_dec_a')

    def test_load_accel_dec_a_not_a_number(self):
        t = TestLoadTracer()
        t.accel_dec_a = []
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'list' object cannot be interpreted as an integer")

    def test_load_no_accelerators(self):
        self._test_missing_attribute(TestLoadTracer, 'accelerators')

    def test_load_accelerator_no_name(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'name', key)

    def test_load_accelerator_no_code(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'code', key)

    def test_load_accelerator_no_c0(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'c0', key)

    def test_load_accelerator_no_c1(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'c1', key)

    def test_load_accelerator_no_counter(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'counter', key)

    def test_load_accelerator_no_inc(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'inc', key)

    def test_load_accelerator_no_loop_time(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'loop_time', key)

    def test_load_accelerator_no_loop_r_inc(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'loop_r_inc', key)

    def test_load_accelerator_no_ear(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'ear', key)

    def test_load_accelerator_no_ear_mask(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'ear_mask', key)

    def test_load_accelerator_no_polarity(self):
        key = lambda t: list(t.accelerators)[-1]
        self._test_missing_attribute(TestLoadTracer, 'polarity', key)

    def test_load_accelerator_code_not_a_list(self):
        t = TestLoadTracer()
        next(iter(t.accelerators)).code = (0, 1)
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(t)
        with self.assertRaises(TypeError) as cm:
            s.load(0, True, False, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "accelerator code is not a list")

class PressTest:
    def test_press_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 5 positional arguments (1 given)")

    def test_press_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press(None, 1, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 5 arguments (6 given)")

    def test_press_invalid_timeout(self):
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(TestKeypressTracer())
        timeout = []
        with self.assertRaises(TypeError) as cm:
            s.press(None, timeout, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 2 must be int, not list")

    def test_press_no_tracer(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.press(None, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_press_keys_not_a_list(self):
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(TestKeypressTracer())
        with self.assertRaises(TypeError) as cm:
            s.press(deque(), 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'keys' is not a list")

    def test_press_no_border(self):
        s, exp_error = self.remove_attribute(TestKeypressTracer, 'border')
        with self.assertRaises(AttributeError) as cm:
            s.press(['0'], 1, None, None, None)
        self.assertEqual(cm.exception.args[0], exp_error)

class PressKeysTest:
    def test_press_keys_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 6 positional arguments (1 given)")

    def test_press_keys_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None, 1, 1, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 6 arguments (7 given)")

    def test_press_keys_invalid_stop(self):
        s = self.simulator_cls([0] * 65536)
        stop = None
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None, stop, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_press_keys_invalid_timeout(self):
        s = self.simulator_cls([0] * 65536)
        timeout = set()
        with self.assertRaises(TypeError) as cm:
            s.press_keys(None, 1, timeout, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 3 must be int, not set")

    def test_press_keys_no_tracer(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.press_keys(None, 1, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_press_keys_no_border(self):
        s, exp_error = self.remove_attribute(TestKeyboardTracer, 'border')
        with self.assertRaises(AttributeError) as cm:
            s.press_keys(['0'], 1, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], exp_error)

    def test_press_keys_keys_not_a_list(self):
        s = self.simulator_cls([0] * 65536)
        t = TestKeyboardTracer()
        s.set_tracer(t)
        t.keys = deque(('1', '2'))
        with self.assertRaises(TypeError) as cm:
            s.press_keys(t.keys, 1, 1, None, None, None)
        self.assertEqual(cm.exception.args[0], "'keys' is not a list")

class TraceTest:
    def test_trace_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.trace(1)
        self.assertEqual(cm.exception.args[0], "function takes exactly 10 positional arguments (1 given)")

    def test_trace_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, 1, 1, True, None, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 10 arguments (11 given)")

    def test_trace_no_tracer(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(ValueError) as cm:
            s.trace(1, 1, 1, 1, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "no tracer set")

    def test_trace_invalid_max_operations(self):
        s = self.simulator_cls([0] * 65536)
        max_operations = None
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, max_operations, 1, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 3 must be int, not None")

    def test_trace_invalid_max_time(self):
        s = self.simulator_cls([0] * 65536)
        max_time = ()
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, 1, max_time, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "argument 4 must be int, not tuple")

    def test_trace_no_border(self):
        s = self.simulator_cls([0] * 65536)
        s.set_tracer(TestTracer())
        with self.assertRaises(AttributeError) as cm:
            s.trace(1, 1, 1, 1, True, None, None, None, None, None)
        self.assertEqual(cm.exception.args[0], "'TestTracer' object has no attribute 'border'")

    def test_trace_exec_map_not_a_set(self):
        s = self.simulator_cls([0] * 65536)
        exec_map = ()
        with self.assertRaises(TypeError) as cm:
            s.trace(1, 1, 1, 1, True, None, exec_map, None, None, None)
        self.assertEqual(cm.exception.args[0], "'exec_map' is not a set")

class RunTest:
    def test_run_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(1, 1, True, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_run_unexpected_arg(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(foo=1)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'foo'")

    def test_run_invalid_start(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_run_invalid_stop(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.run(stop=[])
        self.assertEqual(cm.exception.args[0], "'list' object cannot be interpreted as an integer")

class ExecFrameTest:
    def test_exec_frame_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame()
        self.assertEqual(cm.exception.args[0], "function missing required argument 'fetch_count' (pos 1)")

    def test_exec_frame_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame(1, set(), None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_exec_frame_unexpected_arg(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame(1, bar=1)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'bar'")

    def test_exec_frame_invalid_fetch_count(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame('1')
        self.assertEqual(cm.exception.args[0], "'str' object cannot be interpreted as an integer")

    def test_exec_frame_exec_map_not_a_set(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_frame(1, ())
        self.assertEqual(cm.exception.args[0], "'exec_map' is not a set")

class AcceptInterruptTest:
    def test_accept_interrupt_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.accept_interrupt(None)
        self.assertEqual(cm.exception.args[0], "function takes exactly 3 positional arguments (1 given)")

    def test_accept_interrupt_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.accept_interrupt(None, None, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_accept_interrupt_invalid_prev_pc(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.accept_interrupt(None, None, {})
        self.assertEqual(cm.exception.args[0], "'dict' object cannot be interpreted as an integer")

class ExecWithCBTest:
    def test_exec_with_cb_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_with_cb(1)
        self.assertEqual(cm.exception.args[0], "function missing required argument 'rst16_cb' (pos 2)")

    def test_exec_with_cb_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_with_cb(1, None, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 2 arguments (3 given)")

    def test_exec_with_cb_invalid_stop(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.exec_with_cb([], None)
        self.assertEqual(cm.exception.args[0], "'list' object cannot be interpreted as an integer")

class SetTracerTest:
    def test_set_tracer_too_few_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer()
        self.assertEqual(cm.exception.args[0], "function takes at least 1 positional argument (0 given)")

    def test_set_tracer_too_many_args(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, 1, 1, None)
        self.assertEqual(cm.exception.args[0], "function takes at most 3 arguments (4 given)")

    def test_set_tracer_unexpected_arg(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, baz=2)
        self.assertEqual(cm.exception.args[0], "this function got an unexpected keyword argument 'baz'")

    def test_set_tracer_invalid_in_r_c(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, None)
        self.assertEqual(cm.exception.args[0], "'NoneType' object cannot be interpreted as an integer")

    def test_set_tracer_invalid_ini(self):
        s = self.simulator_cls([0] * 65536)
        with self.assertRaises(TypeError) as cm:
            s.set_tracer(None, True, set())
        self.assertEqual(cm.exception.args[0], "'set' object cannot be interpreted as an integer")

class CSimulatorAPITest(
        CSimulatorAPITestBase, InitTest, AttributesTest, LoadTest, PressTest,
        PressKeysTest, TraceTest, RunTest, ExecFrameTest, AcceptInterruptTest,
        ExecWithCBTest, SetTracerTest
):
    simulator_cls = CSimulator

class CCMIOSimulatorAPITest(
        CSimulatorAPITestBase, InitTest, AttributesTest, LoadTestBase, PressTest,
        PressKeysTest, TraceTest, RunTest, ExecFrameTest, AcceptInterruptTest,
        ExecWithCBTest, SetTracerTest
):
    simulator_cls = CCMIOSimulator
