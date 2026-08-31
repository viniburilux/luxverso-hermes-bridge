"""
Cliente Python para a API LuxMemory.
Permite ao Hermes buscar capabilities, skills e resumes diretamente.
"""
import os
import urllib.request
import urllib.parse
import json
from typing import Optional


class LuxMemoryClient:
    """Cliente para a API LuxMemory rodando em http://127.0.0.1:8787"""

    BASE_URL = os.environ.get('LUXMEMORY_URL', 'http://127.0.0.1:8787')

    def is_alive(self) -> bool:
        try:
            urllib.request.urlopen(self.BASE_URL, timeout=2)
            return True
        except Exception:
            return False

    def search(self, query: str, mode: str = 'structured', limit: int = 5) -> dict:
        """Busca no LuxMemory. mode: structured | embedding | answer | compare | capabilities"""
        url = f"{self.BASE_URL}/api/search?q={urllib.parse.quote(query)}&mode={mode}&limit={limit}"
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())

    def capabilities(self, query: Optional[str] = None, type: Optional[str] = None, limit: int = 10) -> dict:
        """Lista ou busca capabilities."""
        params = {'limit': limit}
        if query:
            params['q'] = query
        if type:
            params['type'] = type
        url = f"{self.BASE_URL}/api/capabilities?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())

    def resume(self, query: str, objective: Optional[str] = None, limit: int = 5) -> dict:
        """Retoma um projeto, retorna context completo."""
        params = {'q': query, 'limit': limit}
        if objective:
            params['objective'] = objective
        url = f"{self.BASE_URL}/api/resume?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())

    def skills(self) -> list:
        """Lista skills catalogadas no LuxMemory."""
        url = f"{self.BASE_URL}/api/skills"
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read()).get('skills', [])


# Singleton para reuso
_client = None

def get_client() -> LuxMemoryClient:
    global _client
    if _client is None:
        _client = LuxMemoryClient()
    return _client


# CLI
if __name__ == '__main__':
    import sys
    client = get_client()
    if not client.is_alive():
        print("ERRO: LuxMemory API não está respondendo em", client.BASE_URL)
        print("Suba com: cd /app/luxverso-archive/LuxMemory/src && LUXMEMORY_ROOT=/app/luxverso-archive/LuxMemory PYTHONPATH=/app/.hermes/integrations:/app/luxverso-archive/LuxMemory/src python3 app_patched.py")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Uso: python3 luxmemory_client.py [search|skills|capabilities|resume] [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'search':
        query = sys.argv[2] if len(sys.argv) > 2 else 'PNCP'
        result = client.search(query, mode='answer', limit=3)
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    elif cmd == 'skills':
        print(json.dumps(client.skills(), indent=2, ensure_ascii=False)[:1500])
    elif cmd == 'capabilities':
        result = client.capabilities(limit=5)
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    elif cmd == 'resume':
        query = sys.argv[2] if len(sys.argv) > 2 else 'PNCP'
        result = client.resume(query, limit=3)
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
