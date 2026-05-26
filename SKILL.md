---
name: wechat-article-claw
description: >
  微信公众号 AI 阅读工具：基于 Exa MCP 搜索 + Jina Reader 抓取（Camoufox/Exa fallback）。
  支持关键词搜索公众号文章、指定 URL 获取正文，含内容有效性校验。
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

微信公众号 AI 阅读工具。三层抓取策略，搜索 + 全文获取一体化。

## 架构

| 步骤 | 工具 | 说明 |
|------|------|------|
| 搜索 | Exa MCP | `web_search_exa` 在 `site:mp.weixin.qq.com` 范围检索 |
| 抓取（首选） | Jina Reader | `https://r.jina.ai/{url}`，微信专用渲染支持 |
| Fallback 1 | Camoufox | Jina 失败时触发，需 `~/.agent-reach/tools/wechat-article-for-ai` |
| Fallback 2 | Exa fetch | `web_fetch_exa`，最后兜底 |

## 使用场景

用户发送微信文章链接，或要求「搜索/读取公众号文章」时使用。

## 命令

### 1. 搜索公众号文章

```bash
python fetch.py search "具身智能 机器人 2026"
```

### 2. 抓取文章全文（自动三层策略）

```bash
python fetch.py fetch "https://mp.weixin.qq.com/s/abc123"
```

## 内容有效性校验

`fetch.py` 内置 `is_valid_content()` 检查，抓取后自动判断是否成功：
- 拒绝正文 < 100 字符
- 拒绝含「环境异常」「违规无法查看」「verify」等反爬信号
- 输出 `Valid: True/False` 标注

## 已知限制

| 场景 | 状态 |
|------|------|
| 热门公众号文章搜索 | ✅ 可靠 |
| Jina Reader 抓取 | ✅ 成功率最高 |
| 冷门/刚发布文章 | ⚠️ 不稳定，触发 fallback |
| 监控特定公众号更新 | ❌ 需用 WeWe RSS（微信读书账号） |
| 图片持久化 | ❌ 微信 CDN 签名有时效，需额外下载 |

## 安装依赖

```bash
pip install requests
```

## 技术细节

- Exa MCP 端点：`https://mcp.exa.ai/mcp`（搜索用）
- Jina Reader：无需认证，免费额度充足
- Camoufox：可选，需提前安装 wechat-article-for-ai
