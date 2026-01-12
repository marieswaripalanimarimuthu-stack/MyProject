import unittest
import sys
from pathlib import Path


# Ensure package paths are importable when running from repo root
ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "mcp-client"
SERVER_PATH = ROOT / "mcp-server"
sys.path.insert(0, str(CLIENT_PATH))
sys.path.insert(0, str(SERVER_PATH))


class TestImports(unittest.TestCase):
    def test_import_mcp_client(self):
        import mcp_client  # noqa: F401

    def test_import_mcp_server(self):
        import mcp_server  # noqa: F401

    def test_import_mcp_server_modules(self):
        import mcp_server.__main__  # noqa: F401
        import mcp_server.query_builder  # noqa: F401


if __name__ == "__main__":
    unittest.main()
