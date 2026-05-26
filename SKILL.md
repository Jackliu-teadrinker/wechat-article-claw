---
name: wechat-article-claw
description: >
  微信公众号 AI 阅读工具：基于微信手机客户端UA绕过验证码，直接抓取正文。
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

## 快速示例

```
用户：「https://mp.weixin.qq.com/s/abc123」
→ python wechat-fetch.py "https://mp.weixin.qq.com/s/abc123"
→ 返回文章正文（纯文本）

用户：「帮我搜一下具身智能相关的公众号文章」
→ python fetch.py search "具身智能 机器人"
→ 返回搜索结果列表（含 URL）
```

## 已知限制

| 场景 | 状态 |
|------|------|
| 普通公众号文章（无验证码） | ✅ 成功率极高 |
| 触发验证码的文章（高阅读量账号） | ✅ 微信UA绕过验证，成功率高 |
| 冷门/刚发布/小众账号文章 | ✅ 微信UA绕过验证，成功率高 |
| 微信图片/视频内容 | ❌ 仅纯文本 |
| 获取阅读量/点赞数 | ❌ 不支持 |
| 监控特定公众号更新 | ❌ 需用 WeWe RSS（微信读书账号） |

## 技术细节

- 微信手机 UA：`MicroMessenger/8.0.47.2504(0x80003003)`
- 仅需 `requests` 库（Python 内置，无需额外依赖）
- 正文提取：从 HTML 的 `id="js_content"` div 中提取纯文本
- 成功率：经实测，四篇之前全部 CRAWL_LIVECRAWL_TIMEOUT 的文章均成功抓取（1.1万字/3449字/1908字/6585字）
