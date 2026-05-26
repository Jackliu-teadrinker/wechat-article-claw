# wechat-article-claw

微信公众号 AI 阅读工具。基于 Exa MCP 直调实现，零配置搜索 + 全文抓取。

## 功能

- **搜索公众号文章**：通过关键词搜索，返回标题、URL、作者、摘要
- **抓取文章全文**：指定 URL，返回完整正文（Markdown 格式）
- **零配置**：不需要 Cookie，不需要 Selenium，直接调 Exa MCP API

## 安装

```bash
pip install requests
```

## 使用方法

### 搜索文章

```bash
python fetch.py search "具身智能 机器人 2026"
```

输出：
```
[+] Found 3 results
--- Result 1 ---
Title: 机器人无法仅靠视觉理解世界
URL: https://mp.weixin.qq.com/s/YglEN7JAfPcyS97gtAiyxw
Author: 值得关注的
Published: N/A
Highlights: 2026年，AI正在从"生成模型时代"走向"世界模型时代"...
```

### 抓取文章

```bash
python fetch.py fetch "https://mp.weixin.qq.com/s/YglEN7JAfPcyS97gtAiyxw"
```

输出：
```
[+] Saved: /tmp/wechat_article.txt
[+] Length: 5897 chars
```

## 工作原理

1. **搜索**：调用 Exa MCP 的 `web_search_exa`，在 `site:mp.weixin.qq.com` 范围内检索
2. **抓取**：调用 Exa MCP 的 `web_fetch_exa`，从 Exa 索引缓存中读取已收录页面的正文

## 已知限制

- 刚发布的新文章、小众公众号文章可能未被 Exa 索引
- 搜索结果按相关度排序，`highlights` 字段是文章摘要片段
- 建议：搜索后发现目标文章，直接用 `fetch` 命令抓全文

## 技术细节

- Exa MCP 端点：`https://mcp.exa.ai/mcp`
- 认证方式：`gh auth token`（自动获取当前 gh 登录用户的 token）
- 响应格式：SSE，需要解析 `data: {...}` 行

## License

MIT
