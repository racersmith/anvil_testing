from anvil import app
import anvil.server
"""
Expose an endpoint to run test at when we are in a debug environment.
"""

# When writing dependencies, add a check fo the app.id to avoid starting multiple endpoints
if 'debug' in app.environment.tags and app.id == 'CCW3SYLSAQHLCF2A':
    test_endpoint = '/test'
    print('Tests can be run here:')
    print(f"{anvil.server.get_app_origin('debug')}{test_endpoint}")
    
    @anvil.server.route(test_endpoint)
    def run() -> anvil.server.HttpResponse:
        from . import _tests
        from .. import auto
        results = auto.run(_tests, quiet=False)
        return anvil.server.HttpResponse(body=results)