import sqlite3, os, shutil

src = os.path.join(os.environ.get('LOCALAPPDATA',''), r'Microsoft\Edge\User Data\Default\Network\Cookies')
dst = os.path.join(os.environ.get('TEMP'), 'edge_cookies_tmp.db')
shutil.copy2(src, dst)

conn = sqlite3.connect(dst)
# 列出所有涉及 wx 相关的 cookie
rows = conn.execute("""
    SELECT host_key, name, value, length(encrypted_value)
    FROM cookies
    WHERE name LIKE '%wx%' OR name LIKE '%token%' OR name LIKE '%uin%'
""").fetchall()
conn.close()

print("All cookies with wx/token/uin:")
for r in rows:
    print(f"  host={r[0]} name={r[1]} valuelen={len(str(r[2]))} enclen={r[3]}")
