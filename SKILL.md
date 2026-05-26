---
name: wechat-article-claw
description: >
  微信公众号 AI 阅读工具：基于 Exa MCP 搜索 + 全文抓取。
  支持关键词搜索公众号文章、指定 URL 获取正文，零配置安装。
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

微信公众号 AI 阅读工具。基于 Exa MCP API 直接实现，零配置安装。

## 工作原理

- **搜索**：`web_search_exa` 在 `site:mp.weixin.qq.com` 范围检索，返回标题、URL、作者、摘要
- **抓取**：`web_fetch_exa` 从 Exa 索引缓存读取已收录页面的正文
- **认证**：自动通过 `gh auth token` 获取，无需手动配置 API Key

## 使用场景

用户发送微信文章链接，或要求「搜索/读取公众号文章」时使用。

## 命令

### 1. 搜索公众号文章

```bash
python fetch.py search "具身智能 机器人 2026"
```

返回：标题、URL、作者、摘要片段（highlights）

### 2. 抓取文章全文

```bash
python fetch.py fetch "https://mp.weixin.qq.com/s/YglEN7JAfPcyS97gtAiyxw"
```

返回：完整正文（Markdown 格式），保存到临时文件

## 快速示例

```
用户：「https://mp.weixin.qq.com/s/abc123」
→ python fetch.py fetch "https://mp.weixin.qq.com/s/abc123"
→ 返回文章正文

用户：「帮我搜一下具身智能相关的公众号文章」
→ python fetch.py search "具身智能 机器人"
→ 返回搜索结果列表（含 URL）
```

## 已知限制

- 刚发布的新文章、小众公众号文章可能未被 Exa 索引
- 搜索结果按相关度排序，`highlights` 是摘要片段，非完整正文
- 如搜索到目标文章，再调用 `fetch` 获取全文

## 安装依赖

```bash
pip install requests
```

仅需 `requests` 库，无其他依赖。

## 技术细节

- Exa MCP 端点：`https://mcp.exa.ai/mcp`（SSE 协议）
- 搜索 API：`web_search_exa`
- 抓取 API：`web_fetch_exa`
- 返回格式：搜索为拼接字符串（需解析），抓取为直接正文
