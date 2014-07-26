from twisted.internet import defer

def deferredList(list_of_deferreds, **kwargs):
    if not 'consumeErrors' in kwargs:
        kwargs['consumeErrors'] = True
    return defer.DeferredList(list_of_deferreds, **kwargs)

def gatherResults(list_of_deferreds):
    return defer.gatherResults(list_of_deferreds, consumeErrors=True)

def retry(times, side_effect, func, *args, **kwargs):
    """
    Call the passed function, and retry the same invocation <times> times if it raises an
        Exception or returns a Failure. Calls side_effect before each retry.

    @param times : Retry the function <times> after the initial invocation.
    @param side_effect: A function to be called before each retry
    """
    d = defer.maybeDeferred(func, *args, **kwargs)

    if times > 0:
        def have_side_effect(f):
            d = defer.maybeDeferred(side_effect)
            d.addBoth(lambda _: f)
            return d
        d.addErrback(have_side_effect)
        d.addErrback(lambda _ : retry(times-1, side_effect, func, *args, **kwargs))
    return d
