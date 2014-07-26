"""
A set of wrapper classes over twisted.application.service

Generally, these have the goal of always returning a Deferred to callers of startService,
or addChildProcess, which should fire when the service is ready for use
"""
import itertools
from zope.interface import implementer

from twisted.application.service import Service as txService
from twisted.application.service import IServiceCollection
from twisted.internet import defer

from bttrtwisted.defer import gatherResults

class Service(txService):

    def __init__(self):
        pass

    def __iter__(self):
        """
        So that Service instances and ServiceCollection instances may be treated
        interchangably, Service must implement __iter__
        """
        yield self

    def setServiceParent(self, parent):
        """
        Re-implements setServiceParent

        Allows disownServiceParent to take time to resolve
        """
        d = defer.succeed(None)
        if self.parent is not None:
            d.addCallback(lambda _: self.disownServiceParent())

        parent = IServiceCollection(parent, parent)
        self.parent = parent

        # pylint can't count the valid length of function args after the Interface adaptation
        #pylint: disable=too-many-function-args
        d.addCallback(lambda _: self.parent.addService(self))
        return d

    def disownServiceParent(self):
        # pylint can't count the valid length of function args after the Interface adaptation
        #pylint: disable=too-many-function-args
        d = self.parent.removeService(self)
        self.parent = None
        return d

    def privilegedStartService(self):
        return defer.succeed(None)

    def startService(self):
        self.running = 1
        return defer.succeed(None)

    def stopService(self):
        self.running = 0
        return defer.succeed(None)


@implementer(IServiceCollection)
class MultiService(Service):
    """
    Re-implements MultiService based on the Deferred guarantees of bttrtwisted.Service
    """

    def __init__(self):
        Service.__init__(self)
        self.services = []
        self.namedServices = {}
        self.parent = None

    def __iter__(self):
        return iter(self.services)

    def privilegedStartService(self):
        d = Service.privilegedStartService(self)
        d.addCallback(gatherResults(service.privilegedStartService()
                                    for service in self))
        return d

    def startService(self):
        d = Service.startService(self)

        d.addCallback(gatherResults(service.startService()
                                    for service in self))
        return d

    def stopService(self):
        """
        Note; this drops the reverse-order stopping of child services in t.a.s.MultiService.
        See TieredMultiService for stopping dependant services in order
        """
        d = Service.stopService(self)
        d.addCallback(gatherResults(service.stopService()
                                    for service in self))
        return d

    def getServiceNamed(self, name):
        return self.namedServices[name]

    def addService(self, service):
        if service.name is not None:
            if service.name in self.namedServices:
                raise RuntimeError("cannot have two services with same name"
                                   " '%s'" % service.name)
            self.namedServices[service.name] = service
        self.services.append(service)
        if self.running:


            d = service.privilegedStartService()
            d.addCallback(lambda _: service.startService())
            return d

    def removeService(self, service):
        if service.name:
            del self.namedServices[service.name]
        self.services.remove(service)
        if self.running:
            # Returning this so as not to lose information from the
            # MultiService.stopService deferred.
            return service.stopService()
        else:
            return None

@implementer(IServiceCollection)
class TieredService(Service):
    """
    Wrapper class for services which should be started (and waited for) in a defined
    order.

    Define tiers by passing a Service to addService. Services which belong to the same
    start/stop tier should be combined into a multiservice, which should then be passed to
    addService
    """
    def __init__(self):
        Service.__init__(self)
        # these may either be bttrtwisted.Services or bttrtwisted.MultiServices
        self.services = []
        self.parent = None

    def __iter__(self):
        return itertools.chain(iter(service) for service in self.services)

    def privilegedStartService(self):
        d = Service.privilegedStartService(self)

        for service in self.services:
            d.addCallback(lambda _: service.privilegedStartService())
        return d

    def startService(self):
        d = Service.startService(self)

        for service in self.services:
            d.addCallback(lambda _: service.startService())
        return d

    def stopService(self):
        """ Note that this changes the .running flag last """
        d = defer.succeed(None)

        for service in self.services:
            d.addCallback(lambda _: service.stopService())

        d.addCallback(Service.stopService(self))
        return d

    def addService(self, service):
        if self.running:
            # If overriding this behaviour, beware race conditions between calling addService
            # or removeService before the startService and stopService deferreds have resolved
            raise RuntimeError("TieredService has been started, you may not addService")
        self.services.append(service)

    def removeService(self, service):
        if self.running:
            # If overriding this behaviour, beware race conditions between calling addService
            # or removeService before the startService and stopService deferreds have resolved
            raise RuntimeError("TieredService has been started, you may not removeService")
        self.services.remove(service)
