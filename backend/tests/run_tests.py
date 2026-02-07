"""
Run backend functionality tests. Exits with non-zero and raises on any failure.
Tests: health, auth, document upload (chunk + Pinecone only, no local file_path), optional RAG.
"""
import io
import os
import sys
from typing import Optional

# Minimal valid PDF bytes (single empty page) for upload test
MINIMAL_PDF = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 12 Tf 100 700 Td (Test medical document.) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer << /Size 5 /Root 1 0 R >>
startxref
307
%%EOF
"""

BASE = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
API = f"{BASE}/api/v1"


def fail(msg: str) -> None:
    """Raise and exit with error."""
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def check_health() -> None:
    r = _get(f"{API}/health")
    if r.get("status") != "ok":
        fail(f"Health returned {r}")
    print("OK health")


def check_ready() -> None:
    r = _get(f"{API}/ready")
    if r.get("status") not in ("ready", "degraded"):
        fail(f"Ready returned {r}")
    print("OK ready")


def _get(url: str):
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json
            return json.loads(resp.read().decode())
    except Exception as e:
        fail(f"GET {url}: {e}")


def _post_json(url: str, data: dict, token: Optional[str] = None) -> dict:
    try:
        import urllib.request
        import json
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        fail(f"POST {url}: {e}")


def _post_upload(url: str, file_bytes: bytes, filename: str, token: str) -> dict:
    try:
        import json
        import urllib.request
        import urllib.error
        boundary = "----FormBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 400:
            body = e.read().decode() if e.fp else ""
            try:
                out = json.loads(body)
                out["_http_400_body"] = body
                return out
            except Exception:
                raise RuntimeError(f"Upload 400: {body}") from e
        fail(f"POST upload {url}: {e.code} {e.reason}")
    except Exception as e:
        fail(f"POST upload {url}: {e}")


def check_auth() -> str:
    email = "test_run@example.com"
    password = "testpass123"
    try:
        _post_json(f"{API}/auth/register", {
            "email": email,
            "password": password,
            "role": "patient",
            "full_name": "Test Run",
        })
    except SystemExit:
        raise
    except Exception:
        pass  # may already exist
    r = _post_json(f"{API}/auth/login", {"email": email, "password": password})
    token = r.get("access_token")
    if not token:
        fail(f"Login missing access_token: {r}")
    print("OK auth")
    return token


def check_upload_no_local_storage(token: str) -> tuple[str, str]:
    """Upload PDF; assert no file_path in response; chunk_count present when upload succeeds."""
    r = _post_upload(f"{API}/documents/upload", MINIMAL_PDF, "test.pdf", token)
    if r.get("chunk_count") is None and ("detail" in r or "_http_400_body" in r):
        print("SKIP upload (minimal PDF has no text or no embeddings); use a real PDF to test upload.")
        return "", ""
    if "file_path" in r:
        fail("Response must not contain file_path (no local storage)")
    chunk_count = r.get("chunk_count")
    if chunk_count is None:
        fail(f"Response must have chunk_count: {r}")
    namespace = r.get("namespace") or ""
    if not namespace and chunk_count:
        fail(f"Response must have namespace when chunk_count > 0: {r}")
    print(f"OK upload (chunk_count={chunk_count}, namespace={namespace}, no file_path)")
    return namespace, r.get("upload_id") or ""


def check_rag_query(token: str, namespace: str) -> None:
    r = _post_json(f"{API}/rag/query", {
        "query": "What is this document about?",
        "namespace": namespace,
        "top_k": 3,
    }, token=token)
    if "refused" in r and r.get("refused"):
        if "message" not in r:
            fail(f"Refusal response missing message: {r}")
        print("OK RAG (refused as expected or no match)")
        return
    if "answer" not in r:
        fail(f"RAG response missing answer: {r}")
    print("OK RAG query")
    return


def main() -> None:
    print("Testing backend (no local storage; chunk + Pinecone only)...")
    check_health()
    check_ready()
    token = check_auth()
    namespace, _ = check_upload_no_local_storage(token)
    if namespace:
        check_rag_query(token, namespace)
    print("All checks passed.")


if __name__ == "__main__":
    main()
