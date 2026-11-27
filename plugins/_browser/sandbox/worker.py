"""Provisioned service anchor; the browser owns a separate cancellable RPC pipe."""
def handle(payload):
    if payload.get('action') == 'status':
        return {'ready': True}
    raise ValueError('Unsupported browser setup action')
