---
name: wechat-article-claw
description: >
  微信公众号 AI 阅读工具：微信手机客户端UA绕过验证码，无需Cookie，无需Selenium。
  支持关键词搜索公众号文章、指定URL获取正文（纯文本），零配置安装。
  当用户发送微信文章链接、或要求搜索/读取公众号文章时激活。
triggers:
  - wechat: 微信/公众号/微信文章/mp.weixin/读一下这个链接/帮我读公众号
  - search_wechat: 搜索公众号/找公众号文章/搜一下这篇
  - fetch_wechat: 抓取微信文章/读取公众号/获取文章正文/文章内容
metadata:
  openclaw:
    homepage: https://github.com/Jackliu-teadrinker/wechat-article-claw
    license: MIT
---

# wechat-article-claw

微信公众号 AI 阅读工具。核心突破：**微信手机客户端 UA 绕过验证码**，无需 Cookie，无需 Selenium，直接获取正文。

## 技术原理

微信的滑块验证码只针对普通浏览器，微信内置浏览器有有效会话不触发验证。通过在请求头中填入微信手机客户端 UA，伪装成微信内置浏览器，直接获取 HTML 正文。

## ⚠️ UA 版本号维护

微信会定期升级客户端，UA 版本号需同步更新。

**当前版本**：`MicroMessenger/8.0.47.2504`（2026-05-26）

**更新方法**：
```bash
# 查询最新版本
python check_wechat_version.py

# 如果发现新版本，手动修改 wechat-fetch.py 中的：
# 1. WX_MOBILE_UA 字符串中的 MicroMessenger/8.0.47.2504
# 2. WX_VERSION = "8.0.47.2504"
```

**版本格式**：`MicroMessenger/{大版本}.{小版本}.{修订版本}({build号})`
例如：`8.0.73.1360` → `MicroMessenger/8.0.73.1360`

**查询最新版本**：
- 微信手机 App → 设置 → 关于微信 → 版本号
- https://www.wxpr.org/

## 架构

| 步骤 | 工具 | 说明 |
|------|------|------|
| 搜索 | Exa MCP | `web_search_exa` 在 `site:mp.weixin.qq.com` 范围检索 |
| 抓取（首选） | wechat-fetch.py | 微信手机 UA 绕过验证码，成功率最高 |
| Fallback | Jina Reader | `https://r.jina.ai/{url}`，普通页面可用 |
| Fallback 2 | Camoufox | `~/.agent-reach/tools/wechat-article-for-ai` |
| Fallback 3 | Exa fetch | `web_fetch_exa`，已收录文章可用 |

## 命令

### 1. 搜索公众号文章

```bash
python fetch.py search "具身智能 机器人 2026"
```

### 2. 抓取文章全文

```bash
python wechat-fetch.py "https://mp.weixin.qq.com/s/abc123"
python wechat-fetch.py "https://mp.weixin.qq.com/s/abc123" "output.txt"
```

### 3. 查询/更新 UA 版本

```bash
python check_wechat_version.py
```

## 快速示例

```
用户：「https://mp.weixin.qq.com/s/abc123」
→ python wechat-fetch.py "https://mp.weixin.qq.com/s/abc123"
→ 返回文章正文（纯文本）

用户：「帮我搜一下具身智能相关的公众号文章」
→ python fetch.py search "具身智能 机器人"
→ 返回搜索结果列表（含 URL）
```

## 场景对比

| 方案 | 成功率 | 速度 | 内容质量 | 适合场景 |
|------|--------|------|---------|---------|
| **微信手机UA（wechat-fetch.py）** | ⭐⭐⭐⭐⭐ | 快 | 纯文本 | ✅ 临时抓取、快速获取文字内容 |
| Exa fetch | ⭐⭐（仅已收录文章）| 快 | 完整 | ⚠️ 4周前的旧文章、备选 |
| Jina Reader | ⭐（微信拦截）| 快 | 较好 | ❌ 微信文章不适用 |
| Camoufox | ⭐⭐⭐（rate limit）| 慢 | 完整HTML+渲染 | ⚠️ 其他方案全部失效时的兜底 |
| WeWe RSS | ⭐⭐⭐⭐（需部署）| 中 | 完整 | ✅ 定期监控某个公众号（需Docker部署） |

## 已知限制

| 场景 | 状态 |
|------|------|
| 普通公众号文章（无验证码） | ✅ 成功率极高 |
| 触发验证码的文章（高阅读量账号） | ✅ 微信UA绕过验证，成功率高 |
| 冷门/刚发布/小众账号文章 | ✅ 微信UA绕过验证，成功率高 |
| 微信图片/视频内容 | ❌ 仅纯文本 |
| 获取阅读量/点赞数 | ❌ 不支持 |
| 定期监控特定公众号 | ⚠️ 需 WeWe RSS（Docker部署）；可用 RSS 阅读器订阅 Exa 搜索结果作为替代 |
