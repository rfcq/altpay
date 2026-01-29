import os

# Ensure templates/static are resolvable when imported as a serverless function
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)

from app import app  # noqa: E402

# Vercel looks for `app` at module scope.

