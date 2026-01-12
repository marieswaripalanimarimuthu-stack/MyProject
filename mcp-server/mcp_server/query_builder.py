import re
from typing import Dict, List, Tuple, Any


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_ident(ident: str) -> str:
    """Validate and return a safe SQL identifier or dotted path like t.col.
    Only allows letters, digits, underscore, dot between parts; no quoting here.
    Raises ValueError if invalid.
    """
    s = str(ident or "").strip()
    if not s:
        raise ValueError("Empty identifier")
    parts = s.split(".")
    for p in parts:
        if not _IDENT_RE.match(p):
            raise ValueError(f"Invalid identifier part: {p}")
    return ".".join(parts)


def _ensure_int(value: Any, name: str) -> int:
    try:
        return int(value)
    except Exception:
        raise ValueError(f"{name} must be an integer")


def _op_sql(op: str) -> str:
    op_map = {
        "=": "=",
        "!=": "!=",
        "<>": "<>",
        ">": ">",
        ">=": ">=",
        "<": "<",
        "<=": "<=",
        "like": "LIKE",
        "in": "IN",
        "between": "BETWEEN",
        "is null": "IS NULL",
        "is not null": "IS NOT NULL",
    }
    k = (op or "").strip().lower()
    if k not in op_map:
        raise ValueError(f"Unsupported operator: {op}")
    return op_map[k]


def build_select_query(spec: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Build a parameterized Oracle SELECT query from a JSON spec.

    Expected spec keys:
      - tables: ["TABLE1", "TABLE2", ...] (required)
      - from: base table name (defaults to first in tables)
      - alias: {"TABLE1": "t1", ...} (optional)
      - distinct: bool (optional)
      - select: ["t1.col", {"expr": "COUNT(*)", "as": "cnt"}] (optional; default ["*"])
      - joins: [{"type":"inner|left|right","left":"t1.id","right":"t2.fk"}] (optional)
      - filters: [{"col":"t1.status","op":"=","value":"OPEN","join":"AND|OR"}] (optional)
      - groupBy: ["t1.col1", ...] (optional)
      - having: [{"col":"COUNT(*)","op":">","value":10}] or raw string via {"raw":"..."}
      - orderBy: [{"expr":"t1.created","dir":"asc|desc"}] (optional)
      - limit: number (optional)
      - offset: number (optional)

    Returns: (sql, params)
    """
    params: Dict[str, Any] = {}
    pseq = 0

    def add_param(val: Any) -> str:
        nonlocal pseq
        pseq += 1
        name = f"p{pseq}"
        params[name] = val
        return f":{name}"

    if not isinstance(spec, dict):
        raise ValueError("spec must be a JSON object")

    tables = spec.get("tables") or []
    if not isinstance(tables, list) or not tables:
        raise ValueError("'tables' must be a non-empty list")

    # Validate and map aliases
    alias_map = {}
    for t in tables:
        _ = _safe_ident(t)
    if spec.get("alias"):
        for k, v in (spec.get("alias") or {}).items():
            alias_map[_safe_ident(k)] = _safe_ident(v)

    base_table = spec.get("from") or tables[0]
    base_table = _safe_ident(base_table)

    distinct = bool(spec.get("distinct"))

    # SELECT clause
    select_items = spec.get("select") or ["*"]
    select_sql: List[str] = []
    for item in select_items:
        if isinstance(item, str):
            select_sql.append(_safe_ident(item) if item != "*" else "*")
        elif isinstance(item, dict):
            if item.get("raw"):
                expr = str(item.get("expr") or "").strip()
                if not expr:
                    raise ValueError("raw select item requires 'expr'")
                alias = str(item.get("as") or "").strip()
                select_sql.append(expr + (f" {alias}" if alias else ""))
            else:
                expr = str(item.get("expr") or "").strip()
                if not expr:
                    raise ValueError("select item requires 'expr'")
                # If expr looks like a dotted ident or *, treat safe; otherwise allow common funcs
                if expr == "*":
                    safe_expr = "*"
                else:
                    try:
                        safe_expr = _safe_ident(expr)
                    except ValueError:
                        # Allow common aggregate patterns only
                        if not re.match(r"^(COUNT|SUM|AVG|MIN|MAX)\s*\((?:\*|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\)$", expr, re.IGNORECASE):
                            raise
                        safe_expr = expr
                alias = str(item.get("as") or "").strip()
                select_sql.append(safe_expr + (f" {alias}" if alias else ""))
        else:
            raise ValueError("Invalid select item")

    # FROM + JOINS
    from_sql = base_table
    if base_table in alias_map:
        from_sql += f" {alias_map[base_table]}"

    join_specs = spec.get("joins") or []
    join_sql: List[str] = []
    for j in join_specs:
        if not isinstance(j, dict):
            raise ValueError("join spec must be object")
        jtype = (j.get("type") or "inner").strip().lower()
        if jtype not in ("inner", "left", "right"):
            raise ValueError("join type must be inner|left|right")
        left = _safe_ident(j.get("left"))
        right = _safe_ident(j.get("right"))
        # Infer table on the right side for the joined table presentation
        right_table = right.split(".")[0]
        jt = {"inner": "INNER JOIN", "left": "LEFT JOIN", "right": "RIGHT JOIN"}[jtype]
        segment = f"{jt} {right_table}"
        if right_table in alias_map:
            segment += f" {alias_map[right_table]}"
        segment += f" ON {left} = {right}"
        join_sql.append(segment)

    # WHERE
    filters = spec.get("filters") or []
    where_sql: List[str] = []
    for f in filters:
        if isinstance(f, dict) and f.get("raw"):
            raw = str(f.get("raw") or "").strip()
            if raw:
                where_sql.append(raw)
            continue
        if not isinstance(f, dict):
            raise ValueError("filter must be object")
        col = _safe_ident(f.get("col"))
        op = _op_sql(f.get("op"))
        joiner = (f.get("join") or "AND").strip().upper()
        if joiner not in ("AND", "OR"):
            raise ValueError("filter.join must be AND|OR")
        clause = None
        if op in ("IS NULL", "IS NOT NULL"):
            clause = f"{col} {op}"
        elif op == "IN":
            vals = f.get("value")
            if not isinstance(vals, list) or not vals:
                raise ValueError("IN operator requires non-empty list 'value'")
            binds = [add_param(v) for v in vals]
            clause = f"{col} IN (" + ", ".join(binds) + ")"
        elif op == "BETWEEN":
            vals = f.get("value")
            if not (isinstance(vals, list) and len(vals) == 2):
                raise ValueError("BETWEEN requires 'value' as [low, high]")
            clause = f"{col} BETWEEN {add_param(vals[0])} AND {add_param(vals[1])}"
        else:
            clause = f"{col} {op} {add_param(f.get('value'))}"
        if where_sql:
            where_sql.append(joiner + " " + clause)
        else:
            where_sql.append(clause)

    # GROUP BY / HAVING
    group_by = spec.get("groupBy") or []
    group_sql = [
        _safe_ident(g) if isinstance(g, str) else None for g in group_by
    ]
    group_sql = [g for g in group_sql if g]

    having_specs = spec.get("having") or []
    having_sql: List[str] = []
    for h in having_specs:
        if isinstance(h, dict) and h.get("raw"):
            raw = str(h.get("raw") or "").strip()
            if raw:
                having_sql.append(raw)
            continue
        if not isinstance(h, dict):
            raise ValueError("having item must be object")
        col = str(h.get("col") or "").strip()
        # Allow aggregate expressions here (COUNT(*), SUM(t.col))
        if not re.match(r"^(?:[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?|COUNT\(\*\)|(?:COUNT|SUM|AVG|MIN|MAX)\s*\([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?\))$", col, re.IGNORECASE):
            raise ValueError("Invalid having expression")
        op = _op_sql(h.get("op"))
        if op in ("IS NULL", "IS NOT NULL"):
            having_sql.append(f"{col} {op}")
        elif op == "IN":
            vals = h.get("value")
            if not isinstance(vals, list) or not vals:
                raise ValueError("IN operator requires non-empty list 'value'")
            binds = [add_param(v) for v in vals]
            having_sql.append(f"{col} IN (" + ", ".join(binds) + ")")
        elif op == "BETWEEN":
            vals = h.get("value")
            if not (isinstance(vals, list) and len(vals) == 2):
                raise ValueError("BETWEEN requires 'value' as [low, high]")
            having_sql.append(f"{col} BETWEEN {add_param(vals[0])} AND {add_param(vals[1])}")
        else:
            having_sql.append(f"{col} {op} {add_param(h.get('value'))}")

    # ORDER BY
    order_by = spec.get("orderBy") or []
    order_sql: List[str] = []
    for o in order_by:
        if isinstance(o, str):
            order_sql.append(_safe_ident(o))
        elif isinstance(o, dict):
            expr = _safe_ident(o.get("expr"))
            dirv = (o.get("dir") or "ASC").strip().upper()
            if dirv not in ("ASC", "DESC"):
                raise ValueError("orderBy.dir must be ASC|DESC")
            order_sql.append(f"{expr} {dirv}")
        else:
            raise ValueError("Invalid orderBy item")

    # LIMIT/OFFSET (Oracle 12c+ style). Inline numerics for compatibility.
    limit = spec.get("limit")
    offset = spec.get("offset")
    if limit is not None:
        limit = _ensure_int(limit, "limit")
    if offset is not None:
        offset = _ensure_int(offset, "offset")

    # Assemble SQL
    sql_parts: List[str] = []
    sql_parts.append("SELECT" + (" DISTINCT" if distinct else ""))
    sql_parts.append(" ".join([", ".join(select_sql), "FROM", from_sql]))
    if join_sql:
        sql_parts.append(" ".join(join_sql))
    if where_sql:
        sql_parts.append("WHERE " + " ".join(where_sql))
    if group_sql:
        sql_parts.append("GROUP BY " + ", ".join(group_sql))
    if having_sql:
        sql_parts.append("HAVING " + " AND ".join(having_sql))
    if order_sql:
        sql_parts.append("ORDER BY " + ", ".join(order_sql))
    if offset is not None and limit is not None:
        sql_parts.append(f"OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY")
    elif limit is not None:
        sql_parts.append(f"FETCH FIRST {limit} ROWS ONLY")

    sql = "\n".join(sql_parts)
    return sql, params


# --- Quick builder: parse simple natural filters like
#     workobjectstatus="pending-ActivationNotification" AND id > 100

_TOKEN_AND = re.compile(r"\band\b", re.IGNORECASE)
_TOKEN_OR = re.compile(r"\bor\b", re.IGNORECASE)


def _split_conditions(text: str) -> Tuple[List[str], List[str]]:
    """Split a where-like text by AND/OR while preserving operator order.
    Returns: (conditions, joins) where joins[i] connects cond[i] to cond[i+1].
    """
    src = (text or "").strip()
    if not src:
        return [], []
    # Simple pass: split on AND/OR tokens; keep sequence of joiners
    parts: List[str] = []
    joins: List[str] = []
    buf = []
    i = 0
    while i < len(src):
        # check AND
        m_and = _TOKEN_AND.match(src, i)
        m_or = _TOKEN_OR.match(src, i)
        if m_and and (not buf or (buf and buf[-1] != ' ')) and (i == 0 or src[i-1].isspace()) and (i+3 == len(src) or src[i+3].isspace()):
            seg = ''.join(buf).strip()
            if seg:
                parts.append(seg)
                joins.append('AND')
            buf = []
            i += 3
            continue
        if m_or and (not buf or (buf and buf[-1] != ' ')) and (i == 0 or src[i-1].isspace()) and (i+2 == len(src) or src[i+2].isspace()):
            seg = ''.join(buf).strip()
            if seg:
                parts.append(seg)
                joins.append('OR')
            buf = []
            i += 2
            continue
        buf.append(src[i])
        i += 1
    last = ''.join(buf).strip()
    if last:
        parts.append(last)
    if parts and joins and len(joins) == len(parts):
        joins = joins[:-1]
    return parts, joins


def _parse_simple_condition(cond: str) -> Dict[str, Any]:
    """Parse a single condition into {col, op, value} or {raw}.
    Supports:
      col = value | col != value | > >= < <=
      col like pattern
      col in (a,b,c)
      col between a and b
      col is null | is not null
    Values can be quoted strings or bare tokens.
    """
    s = (cond or '').strip()
    if not s:
        return {"raw": ""}
    # IS NULL / IS NOT NULL
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+is\s+(not\s+)?null$", s, re.IGNORECASE)
    if m:
        col = _safe_ident(m.group(1))
        if m.group(2):
            return {"col": col, "op": "is not null"}
        return {"col": col, "op": "is null"}

    # IN (...) list
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+in\s*\((.*?)\)$", s, re.IGNORECASE)
    if m:
        col = _safe_ident(m.group(1))
        inside = m.group(2).strip()
        # split by commas respecting quotes lightly
        vals: List[str] = []
        cur = []
        quote = None
        for ch in inside:
            if quote:
                if ch == quote:
                    quote = None
                else:
                    cur.append(ch)
            else:
                if ch in ('"', "'"):
                    quote = ch
                elif ch == ',':
                    v = ''.join(cur).strip()
                    if v:
                        vals.append(v.strip('"\''))
                    cur = []
                else:
                    cur.append(ch)
        v = ''.join(cur).strip()
        if v:
            vals.append(v.strip('"\''))
        return {"col": col, "op": "in", "value": vals}

    # BETWEEN a and b
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+between\s+(.*?)\s+and\s+(.*)$", s, re.IGNORECASE)
    if m:
        col = _safe_ident(m.group(1))
        a = m.group(2).strip().strip('"\'')
        b = m.group(3).strip().strip('"\'')
        return {"col": col, "op": "between", "value": [a, b]}

    # LIKE
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s+like\s+(.*)$", s, re.IGNORECASE)
    if m:
        col = _safe_ident(m.group(1))
        val = m.group(2).strip().strip('"\'')
        return {"col": col, "op": "like", "value": val}

    # Binary ops = != <> > >= < <=
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(=|!=|<>|>=|<=|>|<)\s*(.+)$", s, re.IGNORECASE)
    if m:
        col = _safe_ident(m.group(1))
        op = m.group(2)
        val = m.group(3).strip().strip('"\'')
        return {"col": col, "op": op, "value": val}

    # Fallback raw condition (last resort)
    return {"raw": s}


def build_quick_select(spec: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Quick builder using a single table and a simple filter string.

    spec keys:
      - table: string (required)
      - ask: string like "workobjectstatus=\"pending-ActivationNotification\"" (required)
      - select: list of columns/expressions (optional; default ["*"])
      - limit: int (optional)
      - orderBy: like build_select_query (optional)
    """
    if not isinstance(spec, dict):
        raise ValueError("spec must be object")
    table = _safe_ident(spec.get("table"))
    ask = str(spec.get("ask") or "").strip()
    if not ask:
        raise ValueError("'ask' must be a non-empty string")
    # Split into conditions and joins
    conds, joins = _split_conditions(ask)
    filters: List[Dict[str, Any]] = []
    if not conds:
        raise ValueError("No conditions parsed from 'ask'")
    for idx, c in enumerate(conds):
        f = _parse_simple_condition(c)
        if idx < len(joins):
            f["join"] = joins[idx]
        filters.append(f)

    base_spec: Dict[str, Any] = {
        "tables": [table],
        "from": table,
        "select": spec.get("select") or ["*"],
        "filters": filters,
    }
    if spec.get("orderBy"):
        base_spec["orderBy"] = spec["orderBy"]
    if spec.get("limit") is not None:
        base_spec["limit"] = spec["limit"]

    return build_select_query(base_spec)

