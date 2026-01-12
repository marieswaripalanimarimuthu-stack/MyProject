import argparse
import json
import sys
import urllib.request
import urllib.parse

SERVER_URL = "http://127.0.0.1:8765"


def fetch(project: str, max_results: int, assigned_to: str | None = None, issue_type: str | None = None, status: str | None = None, priority: str | None = None):
    params = {
        "project": project,
        "maxResults": str(max_results),
    }
    if assigned_to:
        params["assignedTo"] = assigned_to
    if issue_type:
        params["type"] = issue_type
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url = f"{SERVER_URL}/jira/issues?{query}"
    with urllib.request.urlopen(url) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def main():
    parser = argparse.ArgumentParser(description="MCP Client for Jira issues")
    # Accept project names with spaces via nargs (optional when using --latest-comment)
    parser.add_argument("--project", nargs="+", required=False, help="Jira project key or name (quotes not required)")
    parser.add_argument("--max", type=int, default=25, help="Max results")
    parser.add_argument("--count", action="store_true", help="Print only the count of matching issues")
    parser.add_argument("--summary", action="store_true", help="Print count first, then list issue details")
    parser.add_argument("--assigned", dest="assigned", choices=["me"], default=None, help="Filter issues assigned to you (me)")
    parser.add_argument("--type", dest="type", default=None, help="Filter by issue type, e.g., Bug")
    parser.add_argument("--status", dest="status", default=None, help="Filter by status, e.g., Open")
    parser.add_argument("--priority", dest="priority", default=None, help="Filter by priority, e.g., High")
    parser.add_argument("--latest-comment", dest="latest_comment_key", default=None, help="Issue key to fetch the latest comment (e.g., CXPOPER-46300)")
    args = parser.parse_args()

    # If latest-comment is requested, bypass list and fetch comment
    if args.latest_comment_key:
        key = args.latest_comment_key
        url = f"{SERVER_URL}/jira/latest-comment?key={urllib.parse.quote(key)}"
        with urllib.request.urlopen(url) as resp:
            data = resp.read().decode("utf-8")
            payload = json.loads(data)
        lc = payload.get("latestComment")
        if not lc:
            print("No comments found.")
            return
        author = ((lc.get("author") or {}).get("displayName") or (lc.get("author") or {}).get("name") or "")
        created = lc.get("created", "")
        body = lc.get("body", "")
        print(f"{key} | {author} | {created}\n{body}")
        return

    if not args.project:
        print("Error: --project is required unless using --latest-comment.")
        return
    project_val = " ".join(args.project) if isinstance(args.project, list) else args.project

    try:
        result = fetch(project_val, args.max, assigned_to=args.assigned, issue_type=args.type, status=args.status, priority=args.priority)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    issues = result.get("issues", [])
    total = result.get("total")

    if args.count:
        if total is not None:
            print(total)
        else:
            print(len(issues))
        return

    if args.summary:
        c = total if total is not None else len(issues)
        print(f"Total defects: {c}")

    if not issues:
        print("No issues found.")
        return

    for issue in issues:
        key = issue.get("key")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        status = (fields.get("status") or {}).get("name", "")
        print(f"{key} | {status} | {summary}")


if __name__ == "__main__":
    main()
