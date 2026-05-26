"""
wechat-article-claw
微信公众号文章搜索与抓取工具
基于 Exa MCP API 直接调用

用法：
  python fetch.py search <关键词>
  python fetch.py fetch <微信URL>
"""
import requests, json, sys, os, re, subprocess

EXA_MCP_URL = "https://mcp.exa.ai/mcp"


def get_token():
    """从 gh auth 获取当前登录用户的 token。"""
    try:
        r = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def exa_call(tool_name, arguments, timeout=30):
    """直接对 Exa MCP 发送 JSON-RPC 请求，解析 SSE 响应。"""
    token = get_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    # 如果有 gh token，加上 Authorization
    if token:
        # Exa MCP 不需要 Authorization，它通过 ghcli-session 认证
        pass

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    }
    r = requests.post(EXA_MCP_URL, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()

    # 强制用 UTF-8 解码（Exa 返回 UTF-8 的 SSE）
    text = r.content.decode("utf-8", errors="replace").strip()
    for line in text.split("\n"):
        if line.startswith("data: "):
            data = json.loads(line[6:])
            if "error" in data:
                return {"error": data["error"]}
            return data.get("result", {})
    return {"error": "no data in response"}


FIELD_STARTS = ("Title: ", "URL: ", "Author: ", "Published: ", "Highlights:")


def parse_search_text(text):
    """解析 web_search_exa 返回的拼接文本。"""
    article = {}
    current_key = None
    current_value = []

    for line in text.split("\n"):
        new_key = None
        stripped = line

        if stripped.startswith("Title: "):
            new_key = "Title"
            stripped = stripped[7:]
        elif stripped.startswith("URL: "):
            new_key = "URL"
            stripped = stripped[5:]
        elif stripped.startswith("Author: "):
            new_key = "Author"
            stripped = stripped[8:]
        elif stripped.startswith("Author:"):
            new_key = "Author"
            stripped = stripped[7:]
        elif stripped.startswith("Published: "):
            new_key = "Published"
            stripped = stripped[11:]
        elif stripped.startswith("Published:"):
            new_key = "Published"
            stripped = stripped[10:]
        elif stripped.startswith("Highlights:"):
            new_key = "Highlights"
            stripped = stripped[11:]
        elif stripped.startswith("Highlights: "):
            new_key = "Highlights"
            stripped = stripped[12:]

        if new_key:
            if current_key:
                article[current_key] = "\n".join(current_value).strip()
            current_key = new_key
            current_value = [stripped] if stripped else []
        else:
            current_value.append(line)

    if current_key:
        article[current_key] = "\n".join(current_value).strip()
    return article


def search_wechat(query, num_results=5):
    """搜索微信公众号文章。"""
    result = exa_call("web_search_exa", {
        "query": f"site:mp.weixin.qq.com {query}",
        "numResults": num_results
    })
    if "error" in result:
        return {"error": result["error"]}

    articles = []
    for item in result.get("content", []):
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        article = parse_search_text(text)
        articles.append({
            "title": article.get("Title", ""),
            "url": article.get("URL", ""),
            "author": article.get("Author", ""),
            "published": article.get("Published", ""),
            "highlights": article.get("Highlights", ""),
        })
    return {"articles": articles}


def fetch_article(url, max_chars=8000):
    """抓取指定 URL 的文章正文。"""
    result = exa_call("web_fetch_exa", {
        "urls": [url],
        "maxCharacters": max_chars
    })
    if "error" in result:
        return {"error": result["error"]}

    content_list = result.get("content", [])
    if not content_list:
        return {"error": "no content returned"}

    first = content_list[0]
    text = first.get("text", "") if isinstance(first, dict) else str(first)
    return {"text": text, "url": url}


def cmd_search(query):
    """执行搜索命令。"""
    print(f"[*] Searching: {query}", flush=True)
    result = search_wechat(query)
    if "error" in result:
        print(f"[!] Error: {result['error']}", flush=True)
        return

    articles = result.get("articles", [])
    out_path = os.path.join(os.environ.get("TEMP", "/tmp"), "wechat_search_result.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\n")
        f.write(f"Found: {len(articles)} results\n\n")
        for i, art in enumerate(articles, 1):
            f.write(f"--- Result {i} ---\n")
            f.write(f"Title: {art['title']}\n")
            f.write(f"URL: {art['url']}\n")
            f.write(f"Author: {art['author']}\n")
            f.write(f"Published: {art['published']}\n")
            hl = art['highlights']
            if hl:
                f.write(f"Highlights: {hl[:600]}\n")
            f.write("\n")
    print(f"[+] Saved: {out_path}", flush=True)
    print(f"[+] Found {len(articles)} results - see file for details", flush=True)
    for i, art in enumerate(articles[:3], 1):
        print(f"  [{i}] {art['title'][:50]} — {art['url'][:60]}", flush=True)


def cmd_fetch(url):
    """执行抓取命令。"""
    print(f"[*] Fetching: {url}", flush=True)
    result = fetch_article(url)
    if "error" in result:
        print(f"[!] Error: {result['error']}", flush=True)
        return

    text = result["text"]
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', url.split("/s/")[1][:30] if "/s/" in url else "article")
    out_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"wechat_{safe_name}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n")
        f.write(text)
    print(f"[+] Saved: {out_path}", flush=True)
    print(f"[+] Length: {len(text)} chars", flush=True)


def main():
    if len(sys.argv) < 3:
        print("Usage:", flush=True)
        print("  python fetch.py search <keyword>", flush=True)
        print("  python fetch.py fetch <wechat_url>", flush=True)
        sys.exit(1)

    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "search":
        cmd_search(arg)
    elif cmd == "fetch":
        cmd_fetch(arg)
    else:
        print(f"[!] Unknown command: {cmd}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
