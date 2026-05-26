"""
check_wechat_version.py
查询微信最新版本并更新 wechat-fetch.py 中的 UA 版本号

用法：python check_wechat_version.py
"""
import requests, re, json, sys
import sys as _sys

_sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 当前使用的版本
CURRENT_VERSION = "8.0.47.2504"

def get_apk_version():
    """从 APK 下载 URL 查询最新版本"""
    try:
        # 尝试多个版本的 APK URL
        for build in ['1360', '1350', '1340']:
            url = f'https://dldir1.qq.com/weixin/android/weixin8027android{build}.apk'
            r = requests.head(url, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                m = re.search(r'weixin(\d+)android(\d+)\.apk', r.url or '', re.I)
                if m:
                    ver, bnum = m.group(1), m.group(2)
                    # 8027 -> 8.0.27
                    major = int(ver[:1])
                    minor = int(ver[1:3])
                    patch = int(ver[3:5])
                    return f"{major}.{minor}.{patch}.{bnum}"
    except:
        pass
    return None

def get_wxpr_version():
    """从 wxpr.org 查询微信版本"""
    try:
        r = requests.get('https://www.wxpr.org/', timeout=10)
        m = re.search(r'MicroMessenger/(\d+\.\d+\.\d+\.\d+)', r.text)
        if m:
            return m.group(1)
    except:
        pass
    return None

def main():
    print(f"Current UA version: MicroMessenger/{CURRENT_VERSION}")
    print()

    android = get_apk_version()
    wxpr = get_wxpr_version()

    latest_info = None
    if android:
        print(f"APK latest: MicroMessenger/{android}")
        latest_info = android
    if wxpr:
        print(f"wxpr.org: MicroMessenger/{wxpr}")
        if not android:
            latest_info = wxpr

    if latest_info and latest_info != CURRENT_VERSION:
        print()
        print(f"[!] NEW VERSION AVAILABLE: {latest_info}")
        print()
        print("To update wechat-fetch.py:")
        print(f"  1. Change WX_MOBILE_UA from MicroMessenger/{CURRENT_VERSION} to MicroMessenger/{latest_info}")
        print(f"  2. Change WX_VERSION = \"{CURRENT_VERSION}\" to WX_VERSION = \"{latest_info}\"")
    elif latest_info:
        print(f"\n[OK] Current version {CURRENT_VERSION} is up to date")
    else:
        print("\nCannot query latest version. Please check manually:")
        print("  WeChat App -> Settings -> About -> Version")

if __name__ == "__main__":
    main()
