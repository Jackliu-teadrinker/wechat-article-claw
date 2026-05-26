"""
从 Edge 浏览器提取微信 Cookie
Chromium 加密方案：cookie 用 AES-256-GCM，密钥用 DPAPI 加密存储
"""
import subprocess, sqlite3, os, json, base64, shutil
from Crypto.Cipher import AES
from Crypto.Util.number import long_to_bytes

EDGE_USER_DATA = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    r"Microsoft\Edge\User Data\Default"
)
EDGE_COOKIE_PATH = os.path.join(EDGE_USER_DATA, "Network", "Cookies")
EDGE_LOCAL_STATE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    r"Microsoft\Edge\User Data\Local State"
)
TEMP_COOKIE_DB = os.path.join(os.environ.get("TEMP"), "edge_cookies_tmp.db")
OUT_FILE = os.path.join(os.environ.get("TEMP"), "wechat_cookies.json")


# ─────────────────────────────────────────
# 1. DPAPI 解密 → 得到 AES key
# ─────────────────────────────────────────

def get_aes_key():
    import win32crypt
    with open(EDGE_LOCAL_STATE, "r", encoding="utf-8") as f:
        state = json.load(f)
    ek = base64.b64decode(state["os_crypt"]["encrypted_key"])
    # 剥掉 DPAPI 前缀
    if ek[:5] == b"DPAPI":
        ek = ek[5:]
    decrypted = win32crypt.CryptUnprotectData(ek, None, None, None, 0)
    return decrypted[1]  # 32 bytes AES key


# ─────────────────────────────────────────
# 2. AES-256-GCM 解密 cookie value
# ─────────────────────────────────────────

def decrypt_cookie_value(encrypted_value: bytes, aes_key: bytes) -> str:
    """
    Chromium 加密格式：v10 + 12-byte nonce + ciphertext + 16-byte auth_tag
    v10: 'v10' or similar prefix, we strip first 3 bytes
    """
    if not encrypted_value or len(encrypted_value) < 28:
        return ""
    # 前 3 字节是版本标识（如 'v10'），剥掉
    data = encrypted_value[3:]
    nonce = data[:12]
    ciphertext = data[12:]
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    try:
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode("utf-8", errors="replace")
    except Exception:
        return ""


# ─────────────────────────────────────────
# 3. 读取并解密 cookies
# ─────────────────────────────────────────

def get_cookies(domain_substr="mp.weixin.qq.com"):
    # 复制 cookie 文件避免 Edge 占用锁
    shutil.copy2(EDGE_COOKIE_PATH, TEMP_COOKIE_DB)

    conn = sqlite3.connect(TEMP_COOKIE_DB)
    rows = conn.execute(
        "SELECT name, encrypted_value, host_key FROM cookies WHERE host_key LIKE ?",
        (f"%{domain_substr}%",)
    ).fetchall()
    conn.close()

    if not rows:
        return {}

    aes_key = get_aes_key()
    cookies = {}
    for name, enc_val_b, host_key in rows:
        if isinstance(enc_val_b, memoryview):
            enc_val_b = bytes(enc_val_b)
        if isinstance(enc_val_b, str):
            enc_val_b = enc_val_b.encode("latin-1")
        value = decrypt_cookie_value(enc_val_b, aes_key)
        if value:
            cookies[name] = value

    return cookies


def main():
    print("[*] Reading Edge cookies for mp.weixin.qq.com ...", flush=True)
    cookies = get_cookies("mp.weixin.qq.com")

    # 重点关注的 Cookie
    target_names = ["wxuin", "wxtokenkey", "appmsglist_opt", "data_basedata_sid", "pgv_pvid", "uuid", "sig"]
    found = {k: cookies.get(k, "") for k in target_names}
    found = {k: v for k, v in found.items() if v}

    print(f"[+] Found {len(found)} target cookies:", flush=True)
    for k, v in found.items():
        print(f"    {k}: {v[:15]}..." if len(v) > 15 else f"    {k}: {v}", flush=True)

    # 保存 JSON
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)

    print(f"\n[+] Cookie dict saved to: {OUT_FILE}", flush=True)
    print("\n=== 直接复制到 fetch.py 使用 ===", flush=True)
    print(json.dumps(found, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
