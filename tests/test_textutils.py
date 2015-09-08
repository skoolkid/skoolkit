from skoolkittest import SkoolKitTestCase
from skoolkit.textutils import find_unquoted, split_unquoted, partition_unquoted

TEST_FIND = (
    # args, kwargs, result
    (('abc', 'b'), {}, 1),
    (('abc', 'd'), {}, 3),
    (('abc', 'd'), {'neg': True}, -1),
    (('abc', 'c'), {'end': 1}, 1),
    (('abc', 'c'), {'end': 1, 'neg': True}, -1),
    (('abc', 'b'), {'start': 1}, 1),
    (('abc', 'a'), {'start': 1}, 3),
    (('abc', 'a'), {'start': 1, 'neg': True}, -1),
    (('c",",d', ','), {}, 4),
    (('abc","d', ','), {}, 7),
    (('abc","d', ','), {'neg': True}, -1),
    (('c",",d', ','), {'end': 3}, 3),
    (('c",",d', ','), {'end': 3, 'neg': True}, -1),
    (('c",",d', ','), {'start': 1}, 4),
    (('c",",d', ','), {'start': 2}, 2),
    (('c",",d', ','), {'start': 3}, 6),
    (('c",",d', ','), {'start': 5}, 6),
    (('c",",d', ','), {'start': 5, 'neg': True}, -1),
)


TEST_SPLIT = (
    # args, result
    (('ab', ','), ['ab']),
    (('a,b', ','), ['a', 'b']),
    (('a":"b', ':'), ['a":"b']),
    (('a":"b:c', ':'), ['a":"b', 'c']),
    (('a-b-c', '-', 1), ['a', 'b-c']),
    (('a"-"b-c-d', '-', 1), ['a"-"b', 'c-d'])
)

TEST_PARTITION = (
    # args, result
    (('ab', ','), ('ab', '', '')),
    (('a,b', ','), ('a', ',', 'b')),
    (('a":"b', ':'), ('a":"b', '', '')),
    (('a":"b:c', ':'), ('a":"b', ':', 'c')),
    (('a":"b', ':', 'x'), ('a":"b', '', 'x')),
    (('a":"b:c', ':', 'x'), ('a":"b', ':', 'c'))
)

class TextUtilsTest(SkoolKitTestCase):
    def setUp(self):
        SkoolKitTestCase.setUp(self)
        self.longMessage = True

    def _test_function(self, exp_result, func, *args, **kwargs):
        args_str = ', '.join([repr(a) for a in args])
        kwargs_str = ', '.join(['{}={!r}'.format(k, v) for k, v in kwargs.items()])
        if kwargs_str:
            kwargs_str = ', ' + kwargs_str
        msg = "{}({}{}) failed".format(func.__name__, args_str, kwargs_str)
        self.assertEqual(exp_result, func(*args, **kwargs), msg)

    def test_find_unquoted(self):
        for args, kwargs, exp_result in TEST_FIND:
            self._test_function(exp_result, find_unquoted, *args, **kwargs)

    def test_split_unquoted(self):
        for args, exp_result in TEST_SPLIT:
            self._test_function(exp_result, split_unquoted, *args)

    def test_partition_unquoted(self):
        for args, exp_result in TEST_PARTITION:
            self._test_function(exp_result, partition_unquoted, *args)
