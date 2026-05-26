"""
wechat-article-claw
微信公众号文章搜索与抓取工具

架构：
  search  → Exa MCP（搜索，保持现状）
  read   → Jina Reader（首选）
  read   → Camoufox（fallback，Jina 失败时）
  read   → Exa fetch（最后 fallback）
"""
import requests, json, sys, os, re, subprocess, time

EXA_MCP_URL = "https://mcp.exa.ai/mcp"
TEMP_DIR = os.environ.get("TEMP", "/tmp")

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────

def get_token():
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
    """直调 Exa MCP JSON-RPC，解析 SSE 响应。"""
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments}
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    r = requests.post(EXA_MCP_URL, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace").strip()
    for line in text.split("\n"):
        if line.startswith("data: "):
            data = json.loads(line[6:])
            if "error" in data:
                return {"error": data["error"]}
            return data.get("result", {})
    return {"error": "no data in response"}


def is_valid_content(text: str) -> bool:
    """内容有效性校验。微信反爬/违规/正文太短均返回 False。"""
    if not text or len(text.strip()) < 100:
        return False
    rejection_signals = [
        "环境异常",
        "打开次数已到限制",
        "此内容因违规无法查看",
        "verify",
        "无法访问",
        "No article found",
        "CRAWL_LIVECRAWL_TIMEOUT",
    ]
    return not any(s in text for s in rejection_signals)


# ─────────────────────────────────────────
# 搜索（Exa MCP，保持现状）
# ─────────────────────────────────────────

def parse_search_text(text: str) -> dict:
    """解析 web_search_exa 返回的拼接文本。"""
    article = {}
    current_key = None
    current_value = []

    for line in text.split("\n"):
        new_key = None
        stripped = line

        if stripped.startswith("Title: "):
            new_key = "Title"; stripped = stripped[7:]
        elif stripped.startswith("URL: "):
            new_key = "URL"; stripped = stripped[5:]
        elif stripped.startswith("Author: "):
            new_key = "Author"; stripped = stripped[8:]
        elif stripped.startswith("Author:"):
            new_key = "Author"; stripped = stripped[7:]
        elif stripped.startswith("Published: "):
            new_key = "Published"; stripped = stripped[11:]
        elif stripped.startswith("Published:"):
            new_key = "Published"; stripped = stripped[10:]
        elif stripped.startswith("Highlights:"):
            new_key = "Highlights"; stripped = stripped[11:]
        elif stripped.startswith("Highlights: "):
            new_key = "Highlights"; stripped = stripped[12:]

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


def search_wechat(query: str, num_results: int = 5) -> dict:
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
            "title":   article.get("Title", ""),
            "url":     article.get("URL", ""),
            "author":  article.get("Author", ""),
            "published": article.get("Published", ""),
            "highlights": article.get("Highlights", ""),
        })
    return {"articles": articles}


# ─────────────────────────────────────────
# 抓取
# ─────────────────────────────────────────

def fetch_jina(url: str) -> str:
    """Jina Reader 抓取，最简单直接。"""
    jina_url = f"https://r.jina.ai/{url}"
    headers = {
        "Accept": "text/markdown",
        "X-No-Cache": "true",
        "X-Return-Format": "text"
    }
    r = requests.get(jina_url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_camoufox(url: str) -> str:
    """Camoufox fallback——需要 wechat-article-for-ai 工具已安装。"""
    tool_path = os.path.expanduser("~/.agent-reach/tools/wechat-article-for-ai")
    main_py = os.path.join(tool_path, "main.py")
    if not os.path.exists(main_py):
        return "[Camoufox not installed at ~/.agent-reach/tools/wechat-article-for-ai]"

    r = subprocess.run(
        [sys.executable, main_py, url],
        capture_output=True, text=True, timeout=60,
        encoding="utf-8", errors="replace"
    )
    if r.returncode != 0:
        return f"[Camoufox error: {r.stderr[:200]}]"
    return r.stdout


def fetch_exa(url: str, max_chars: int = 10000) -> str:
    """Exa fetch 最后 fallback。"""
    result = exa_call("web_fetch_exa", {
        "urls": [url],
        "maxCharacters": max_chars
    })
    if "error" in result:
        return f"[Exa error: {result['error']}]"

    content_list = result.get("content", [])
    if not content_list:
        return "[Exa returned empty content]"
    first = content_list[0]
    return first.get("text", "") if isinstance(first, dict) else str(first)


def fetch_article(url: str) -> dict:
    """
    三层抓取策略：
      1. Jina Reader（最快，成功率最高）
      2. Camoufox（Jina 失败时 fallback）
      3. Exa fetch（最后 fallback）
    返回 {"text": str, "source": str}
    """
    # 1. Jina Reader
    try:
        text = fetch_jina(url)
        if is_valid_content(text):
            return {"text": text, "source": "jina"}
    except Exception as e:
        pass

    # 2. Camoufox
    try:
        text = fetch_camoufox(url)
        if is_valid_content(text):
            return {"text": text, "source": "camoufox"}
    except Exception:
        pass

    # 3. Exa fetch
    text = fetch_exa(url)
    if is_valid_content(text):
        return {"text": text, "source": "exa"}

    return {"text": text, "source": "all-failed"}


# ─────────────────────────────────────────
# 命令行接口
# ─────────────────────────────────────────

def cmd_search(query: str):
    print(f"[*] Searching: {query}", flush=True)
    result = search_wechat(query)
    if "error" in result:
        print(f"[!] Error: {result['error']}", flush=True)
        return

    articles = result.get("articles", [])
    out_path = os.path.join(TEMP_DIR, "wechat_search_result.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\nFound: {len(articles)} results\n\n")
        for i, art in enumerate(articles, 1):
            f.write(f"--- Result {i} ---\n")
            f.write(f"Title: {art['title']}\n")
            f.write(f"URL: {art['url']}\n")
            f.write(f"Author: {art['author']}\n")
            f.write(f"Published: {art['published']}\n")
            hl = art["highlights"]
            if hl:
                f.write(f"Highlights: {hl[:600]}\n")
            f.write("\n")
    print(f"[+] Saved: {out_path}", flush=True)
    print(f"[+] Found {len(articles)} results", flush=True)
    for i, art in enumerate(articles[:3], 1):
        print(f"  [{i}] {art['title'][:50]}", flush=True)


def cmd_fetch(url: str):
    print(f"[*] Fetching: {url}", flush=True)
    r = fetch_article(url)

    text = r["text"]
    source = r["source"]
    valid = is_valid_content(text)

    safe_name = re.sub(
        r'[<>:"/\\|?*]', "_",
        url.split("/s/")[1][:30] if "/s/" in url else "article"
    )
    out_path = os.path.join(TEMP_DIR, f"wechat_{safe_name}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\nSource: {source}\nValid: {valid}\n\n")
        f.write(text)

    print(f"[+] Saved: {out_path}", flush=True)
    print(f"[+] Length: {len(text)} chars | Source: {source} | Valid: {valid}", flush=True)

    if not valid:
        print("[!] Warning: content may be invalid or blocked", flush=True)


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
