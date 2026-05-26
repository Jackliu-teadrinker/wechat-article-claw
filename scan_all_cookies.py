"""全面扫描 Edge 所有 Cookie，不遗漏任何域名。"""
import sqlite3, os, shutil, json, base64
from Crypto.Cipher import AES

EDGE_USER_DATA = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Edge\User Data\Default")
EDGE_COOKIE_PATH = os.path.join(EDGE_USER_DATA, "Network", "Cookies")
EDGE_LOCAL_STATE = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Edge\User Data\Local State")
TEMP_COOKIE_DB = os.path.join(os.environ.get("TEMP"), "edge_cookies_tmp2.db")
OUT_FILE = os.path.join(os.environ.get("TEMP"), "wechat_cookies.json")


def get_aes_key():
    import win32crypt
    with open(EDGE_LOCAL_STATE, "r", encoding="utf-8") as f:
        state = json.load(f)
    ek = base64.b64decode(state["os_crypt"]["encrypted_key"])
    if ek[:5] == b"DPAPI":
        ek = ek[5:]
    return win32crypt.CryptUnprotectData(ek, None, None, None, 0)[1]


def decrypt_value(encrypted_value: bytes, aes_key: bytes) -> str:
    if not encrypted_value or len(encrypted_value) < 15:
        return ""
    data = encrypted_value[3:]  # strip 'v10' prefix
    nonce, ciphertext = data[:12], data[12:]
    try:
        return AES.new(aes_key, AES.MODE_GCM, nonce=nonce).decrypt(ciphertext).decode("utf-8", errors="replace")
    except Exception:
        return ""


def get_all_cookies():
    shutil.copy2(EDGE_COOKIE_PATH, TEMP_COOKIE_DB)
    conn = sqlite3.connect(TEMP_COOKIE_DB)
    rows = conn.execute("SELECT host_key, name, encrypted_value FROM cookies").fetchall()
    conn.close()

    aes_key = get_aes_key()
    result = {}
    for host_key, name, enc_val in rows:
        if isinstance(enc_val, memoryview):
            enc_val = bytes(enc_val)
        if isinstance(enc_val, str):
            enc_val = enc_val.encode("latin-1")
        value = decrypt_value(enc_val, aes_key)
        if value:
            result[(host_key, name)] = value
    return result


def main():
    print("[*] Scanning ALL Edge cookies for WeChat-related entries...", flush=True)
    all_cookies = get_all_cookies()

    # 打印所有涉及微信/qq 的条目
    wx_cookies = {
        (host, name): val
        for (host, name), val in all_cookies.items()
        if any(d in host for d in ["weixin", "wechat", "qq.com", "wechatapp"])
    }

    print(f"\n[+] Found {len(wx_cookies)} WeChat-related cookies:", flush=True)
    for (host, name), val in sorted(wx_cookies.items()):
        preview = val[:30].replace("\n", " ")
        print(f"  [{host}] {name} = {preview}", flush=True)

    # 打印所有独特域名（调试用）
    all_hosts = set(host for (host, _) in all_cookies.keys())
    print(f"\n[+] Total unique domains: {len(all_hosts)}", flush=True)
    print("All domains:", sorted(all_hosts), flush=True)

    # 重点输出 wxuin / wxtokenkey
    target = {k: v for (h, k), v in wx_cookies.items()
              if k in ["wxuin", "wxtokenkey", "appmsglist_opt", "data_basedata_sid", "pgv_pvid", "uuid"]}
    if target:
        print(f"\n[+] Target cookies found:", flush=True)
        for k, v in target.items():
            print(f"    {k}: {v[:20]}...", flush=True)
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(target, f, ensure_ascii=False, indent=2)
        print(f"[+] Saved to: {OUT_FILE}", flush=True)
    else:
        print("\n[!] No wxuin/wxtokenkey found in Edge cookies.", flush=True)
        print("    Are you logged into mp.weixin.qq.com in Edge?", flush=True)


if __name__ == "__main__":
    main()
