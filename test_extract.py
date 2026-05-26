import requests, re

WX_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36 "
    "MicroMessenger/8.0.47.2504(0x80003003) NetType/WIFI Language/zh_CN"
)

url = 'https://mp.weixin.qq.com/s/TdENUw0oL6cqiIy1GGyZCQ'
headers = {'User-Agent': WX_MOBILE_UA, 'Accept': 'text/html'}
r = requests.get(url, headers=headers, timeout=20)
html = r.text

print(f"HTML length: {len(html)}")

# Strategy: find js_content (the article body div)
# Pattern: id="js_content" class="rich_media_content  ... all content ... id="js_pc_qr_code"
patterns = [
    r'id="js_content"[^>]*>(.*?)id="js_pc_qr_code"',
    r'class="rich_media_content"[^>]*>(.*?)(?:id="js_pc_qr"|<div class="rich_media_extra")',
    r'id="js_content"(.*?)(?=<div[^>]*id="js_pc_qr_code"|<!-- end -->|<div class="rich_media_extra")',
]

text = None
for i, pattern in enumerate(patterns):
    m = re.search(pattern, html, re.DOTALL)
    if m:
        content = m.group(1)
        # Strip all HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        # Clean whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text).strip()
        print(f"Pattern {i+1} matched, text length: {len(text)}")
        break

if text and len(text) > 100:
    print("\n--- Preview (first 800 chars) ---")
    print(text[:800])
else:
    print("No content extracted, trying broader search...")
    # Last resort: extract between known markers
    start = html.find('id="js_content"')
    end = html.find('id="js_pc_qr_code"')
    if start > 0 and end > 0:
        content = html[start+16:end]
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).strip()
        print(f"Direct extraction: {len(text)} chars")
        print(text[:500])
    else:
        print("Could not find extraction points")
        # Just show what we have around js_content
        idx = html.find('js_content')
        print("Around js_content:", html[idx:idx+300])
