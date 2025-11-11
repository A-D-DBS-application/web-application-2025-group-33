import os
from supabase import create_client
from flask import current_app


def make_supabase_client(app=None):
    """Create and return a Supabase client. Use service role key for server-side ops.
    Attach to app.supabase for handlers to use.
    """
    if app is None:
        app = current_app

    url = app.config.get('SUPABASE_URL')
    key = app.config.get('SUPABASE_SERVICE_ROLE_KEY') or app.config.get('SUPABASE_KEY')
    if not url or not key:
        raise RuntimeError('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) must be set in config')

    client = create_client(url, key)
    return client
