def enforce_user_agent(f):
    """
    View decorator enforcing feedback from the latest beta users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    def wrapped(request, *args, **kwargs):
        if request.method != 'GET' or not settings.ENFORCE_USER_AGENT:
            return f(request, *args, **kwargs)
    return wrapped
