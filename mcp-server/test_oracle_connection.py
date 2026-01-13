import os
import sys

try:
    import oracledb
except Exception as e:
    print("[ERROR] python-oracledb is not installed. Run: pip install -r mcp-server/requirements.txt", file=sys.stderr)
    sys.exit(2)


def get_env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        print(f"[ERROR] Missing environment variable: {name}", file=sys.stderr)
        sys.exit(2)
    return v


def main() -> int:
    dsn = get_env("ORACLE_DSN")
    user = get_env("ORACLE_USER")
    # Don't echo the password
    pwd = os.environ.get("ORACLE_PASSWORD", "")
    if not pwd:
        print("[ERROR] Missing environment variable: ORACLE_PASSWORD", file=sys.stderr)
        return 2

    print(f"[INFO] Connecting to Oracle ({dsn}) as {user}...")
    try:
        conn = oracledb.connect(user=user, password=pwd, dsn=dsn)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}", file=sys.stderr)
        return 1

    try:
        with conn.cursor() as cur:
            cur.execute("select sys_context('USERENV','SESSION_USER'), sysdate from dual")
            row = cur.fetchone()
            who, when = row[0], row[1]
            print(f"[OK] Connected as {who}; server time: {when}")
            cur.execute("select 1 from dual")
            _ = cur.fetchone()
            print("[OK] Test query succeeded (select 1 from dual)")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
