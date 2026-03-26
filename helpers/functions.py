import inspect

def safe_call(func, *args, **kwargs):
    sig = inspect.signature(func)

    bound_args = []
    bound_kwargs = {}

    params = sig.parameters

    # Check if function accepts *args / **kwargs
    accepts_var_args = any(p.kind == p.VAR_POSITIONAL for p in params.values())
    accepts_var_kwargs = any(p.kind == p.VAR_KEYWORD for p in params.values())

    # Handle positional args
    if accepts_var_args:
        bound_args = args
    else:
        max_positional = sum(
            1
            for p in params.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        )
        bound_args = args[:max_positional]

    # Handle kwargs
    if accepts_var_kwargs:
        bound_kwargs = kwargs
    else:
        bound_kwargs = {k: v for k, v in kwargs.items() if k in params}

    return func(*bound_args, **bound_kwargs)
