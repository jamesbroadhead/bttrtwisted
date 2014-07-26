from __future__ import print_function
from twisted.internet import defer
from twisted.python import log
from twisted.trial import unittest

from bttrtwisted.defer import retry
from bttrtwisted_tests.utils import TestException

class TestRetry(unittest.TestCase):

    def setUp(self):
        self.call_counter = 0
        self.succeed_after = 0

    def _verify_args_and_fail(self, a, b, kw0='should never be set', kw1=None, kw2='d'):
        """
        verifies the args passed, then return a failure
        """
        self.assertEqual(a, 'a')
        self.assertEqual(b, 'b')
        self.assertEqual(kw0, 'should never be set')
        self.assertEqual(kw1, 'c')
        self.assertEqual(kw2, 'd')

        self.call_counter += 1
        return defer.fail(TestException('oh no'))

    def _fail_until_call_count(self, a, b, kw0='should never be set', kw1=None, kw2='d'):
        """
        method which fails until the called more than self.succeed_after times
        (it also verifies the args passed each time)
        """
        f = self._verify_args_and_fail(a, b, kw0=kw0, kw1=kw1, kw2=kw2)

        if self.call_counter >= self.succeed_after:
            f.addErrback(lambda _: None)
        return f

    def test_no_retries_does_not_retry(self):
        d = retry(0, lambda _: None, self._verify_args_and_fail, 'a', 'b', kw1='c')
        self.assertFailure(d, TestException)
        d.addCallback(lambda _: self.assertEqual(self.call_counter, 1))
        return d

    def test_one_retry_retries_once(self):
        d = retry(1, lambda _: None, self._verify_args_and_fail, 'a', 'b', kw1='c')
        self.assertFailure(d, TestException)
        d.addCallback(lambda _: self.assertEqual(self.call_counter, 2))
        return d

    def test_immediate_success_does_not_retry(self):
        self.succeed_after = 0
        d = retry(1, lambda _: None, self._fail_until_call_count, 'a', 'b', kw1='c')
        d.addCallback(lambda _: self.assertEqual(self.call_counter, 1))
        return d

    def test_retries_until_success(self):
        self.succeed_after = 3
        d = retry(2, lambda _: None, self._fail_until_call_count, 'a', 'b', kw1='c')
        d.addCallback(lambda _: self.assertEqual(self.call_counter, 3))
        return d

    def test_does_not_retry_beyond_success(self):
        self.succeed_after = 3
        d = retry(10, lambda _: None, self._fail_until_call_count, 'a', 'b', kw1='c')
        d.addCallback(lambda _: self.assertEqual(self.call_counter, 3))
        return d
