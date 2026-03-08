# API 触发方式说明

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install anthropic schedule python-dotenv

# 创建配置文件
echo "ANTHROPIC_API_KEY=sk-ant-你的密钥" > .env
```

### 2. 立即执行一次分析

```bash
python scripts/trigger.py --run-now --skill-dir ./aluminum-investment-agent
```

### 3. 启动定时模式（长期运行）

```bash
# 前台运行
python scripts/trigger.py --schedule

# 后台运行（Linux/Mac）
nohup python scripts/trigger.py --schedule > logs/agent.log 2>&1 &
```

### 4. 只检查预警条件

```bash
python scripts/trigger.py --check-alert
```

---

## Cron 配置（推荐）

```cron
# 编辑 crontab: crontab -e

# 每周五16:30执行完整周报
30 16 * * 5 /usr/bin/python3 /path/to/scripts/trigger.py --run-now >> /path/to/logs/weekly.log 2>&1

# 每个工作日15:30检查预警
30 15 * * 1-5 /usr/bin/python3 /path/to/scripts/trigger.py --check-alert >> /path/to/logs/alert.log 2>&1

# 重大事件窗口期每天多检查一次（如财报季）
0 9 * * 1-5 /usr/bin/python3 /path/to/scripts/trigger.py --check-alert >> /path/to/logs/alert.log 2>&1
```

---

## Claude.ai Project 方式（无需编程）

如果不想写代码，可以用 Claude.ai 的 Project 功能：

1. 创建一个名为「铝市投研」的 Project
2. 将 `SKILL.md`、`references/` 下的所有文件上传到 Project 知识库
3. 每次需要分析时，直接发送：
   ```
   执行铝行业投资分析工作流，今天是YYYY-MM-DD
   ```
4. 若需要周报，发送：
   ```
   生成本周铝行业投资周报
   ```

---

## 报告存储建议

```
reports/
├── 2026-02-21-weekly.md      ← 按日期命名
├── 2026-02-14-weekly.md
├── alerts/
│   ├── 2026-02-10-alert.md   ← 预警触发记录
│   └── ...
└── archive/
    └── 2025/
```

---

## 成本估算

每次完整分析（使用 claude-opus-4-6）：
- 预计输入 tokens：约 8,000-12,000（含 system prompt）
- 预计输出 tokens：约 3,000-5,000
- 预计费用：约 $0.15-0.25 / 次

每次预警检查（使用 claude-sonnet-4-6）：
- 预计费用：约 $0.02-0.05 / 次

按每周1次完整分析 + 5次预警检查：
- 月费用估算：约 $4-6 / 月

---

## 常见问题

**Q: 搜索数据需要联网权限吗？**
A: 是的，Claude API 本身不含 web_search 工具。需要在 API 调用时通过 tools 参数启用 web_search，或在 claude.ai 的 Project 中默认启用。使用 API 时在 client.messages.create 中添加：
```python
tools=[{"type": "web_search_20250305", "name": "web_search"}]
```

**Q: 报告质量取决于什么？**
A: 主要取决于搜索能否获取到最新数据。如果特定数据源无法获取，Agent 会用最近一次已知值代替并标注。

**Q: 可以修改分析的侧重点吗？**
A: 直接编辑 `SKILL.md` 中的阶段说明，或在 `references/profit-model.md` 中更新最新的基础参数（如新年报出来后）。
