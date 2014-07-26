from twisted.trial import unittest

from bttrtwisted.service import Service

class TestService(unittest.TestCase):

    def setUp(self):
        self.s = Service()

    def test_iterator(self):
        result = [ i for i in iter(self.s) ]
        self.assertEqual(result, [self.s])

    def test_privilegedStartService_returns_a_deferred(self):
        d = self.s.privilegedStartService()
        d.addCallback(self.assertEqual, None)
        return d

    def test_startService_returns_a_deferred(self):
        d = self.s.startService()
        d.addCallback(self.assertEqual, None)
        return d

    def test_stopService_returns_a_deferred(self):
        d = self.s.stopService()
        d.addCallback(self.assertEqual, None)
        return d


