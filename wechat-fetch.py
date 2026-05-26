"""
wechat-fetch.py
微信公众号文章抓取——通过微信手机客户端UA绕过验证码

核心方法：用微信内置浏览器的 UA 伪装已登录 Session，直接绕过滑块验证码。

═══════════════════════════════════════════════════════════════
⚠️ UA 版本号维护（Jack 2026-05-26）
═══════════════════════════════════════════════════════════════
当前版本：MicroMessenger/8.0.47.2504

更新方法：
  1. 查询微信 Android 最新版本
     - 微信手机 App -> 设置 -> 关于微信 -> 版本号
     - 或搜索 https://www.wxpr.org/ 查看最新版本
  2. UA 格式：MicroMessenger/{大版本}.{小版本}.{修订版本}({build号})
     - 例如：8.0.73.1360 对应 MicroMessenger/8.0.73.1360
  3. 修改下方 WX_MOBILE_UA 常量中的 MicroMessenger 版本号

版本历史：
  2026-05-26  MicroMessenger/8.0.47.2504  初始版本

监控脚本：运行 python check_wechat_version.py 自动查询最新版本
═══════════════════════════════════════════════════════════════
"""
import requests, re, sys, os

# ⚠️ 每次微信更新后，手动修改这里
WX_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36 "
    "MicroMessenger/8.0.47.2504(0x80003003) NetType/WIFI Language/zh_CN"
)
WX_VERSION = "8.0.47.2504"
TIMEOUT = 20


def extract_text_from_html(html: str) -> str:
    """
    从微信文章HTML中提取纯正文。
    微信文章正文在 id="js_content" 的div内。
    """
    # 策略1: id="js_content" 到 id="js_pc_qr_code"
    m = re.search(
        r'id="js_content"[^>]*>(.*?)id="js_pc_qr_code"',
        html, re.DOTALL
    )
    if m:
        content = m.group(1)
    else:
        # 策略2: class="rich_media_content"
        m = re.search(
            r'class="rich_media_content"[^>]*>(.*?)(?:id="js_pc_qr"|<div class="rich_media_extra")',
            html, re.DOTALL
        )
        content = m.group(1) if m else html

    # 去掉所有HTML标签
    text = re.sub(r'<[^>]+>', '', content)
    # 清理多余空白，保留段落结构
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text


def fetch_wechat_article(url: str) -> tuple[str, str]:
    """
    抓取微信公众号文章正文。
    返回 (纯文本, 来源标识)
    """
    if not url.startswith('http'):
        url = 'https://' + url

    headers = {
        "User-Agent": WX_MOBILE_UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
    }

    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
    except Exception as e:
        return "", f"request-error: {e}"

    html = r.text

    # 检测是否触发了验证码
    if '环境异常' in html[:2000] or 'verify' in html[:500].lower():
        return "", "captcha-detected"

    text = extract_text_from_html(html)

    if not text or len(text.strip()) < 100:
        return "", "extraction-failed"

    return text, f"wechat-mobile-ua ({WX_VERSION})"


def is_valid(text: str) -> bool:
    if not text or len(text.strip()) < 100:
        return False
    rejection = ["环境异常", "打开次数已到限制", "此内容因违规无法查看",
                 "verify", "无法访问", "No article found", "CRAWL_LIVECRAWL_TIMEOUT"]
    return not any(s in text for s in rejection)


def main():
    if len(sys.argv) < 2:
        print("Usage: python wechat-fetch.py <wechat_url> [output_path]", flush=True)
        sys.exit(1)

    url = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"[*] Fetching: {url}", flush=True)
    text, source = fetch_wechat_article(url)

    if not is_valid(text):
        print(f"[!] Failed: {source}", flush=True)
        if text:
            print("[!] Preview:", text[:300], flush=True)
        sys.exit(1)

    if not out_path:
        safe_id = re.sub(
            r'[<>:"/\\|?*]', '_',
            url.split("/s/")[1][:30] if "/s/" in url else "article"
        )
        out_path = os.path.join(os.environ.get("TEMP", "/tmp"), f"wechat_{safe_id}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\nSource: {source}\n\n")
        f.write(text)

    print(f"[+] Saved: {out_path}", flush=True)
    print(f"[+] Length: {len(text)} chars | Source: {source}", flush=True)
    print(f"\n--- Preview (first 500 chars) ---", flush=True)
    print(text[:500], flush=True)


if __name__ == "__main__":
    main()
