# API 触发方式说明

## 快速开始

### 1. 环境准备

```bash
pip install anthropic schedule python-dotenv

echo "ANTHROPIC_API_KEY=sk-ant-your-key" > .env
```

### 2. 立即执行一次板块分析

```bash
python3 scripts/trigger.py --run-now --skill-dir ./macro-sector-rotation-agent
```

### 3. 启动定时模式

```bash
python3 scripts/trigger.py --schedule

# 后台运行
nohup python3 scripts/trigger.py --schedule > logs/macro-agent.log 2>&1 &
```

### 4. 只检查事件预警

```bash
python3 scripts/trigger.py --check-alert
```

可选参数：
- `--report-model <model>` 自定义周报模型
- `--alert-model <model>` 自定义预警模型
- `--disable-web-search` 在环境不支持工具调用时禁用检索工具

---

## Cron 配置（示例）

```cron
# 每周日21:00执行周报（周一前准备）
0 21 * * 0 /usr/bin/python3 /path/to/scripts/trigger.py --run-now >> /path/to/logs/weekly.log 2>&1

# 每个交易日14:50检查事件预警
50 14 * * 1-5 /usr/bin/python3 /path/to/scripts/trigger.py --check-alert >> /path/to/logs/alert.log 2>&1
```

---

## Claude Project 方式（无需编程）

1. 创建 Project（例如：宏观板块轮动）
2. 上传 `SKILL.md` 和 `references/` 下所有 `.md`
3. 每周执行时发送：

```
执行本周宏观板块轮动分析，今天是YYYY-MM-DD
```

4. 事件驱动时发送：

```
基于最新政策和国际局势，更新板块配置建议
```

---

## 常见问题

**Q: 数据不全怎么办？**  
A: 使用最近一期可得数据并明确标注日期与替代来源。

**Q: 需要 web_search 吗？**  
A: 建议启用。脚本会优先尝试 `web_search`，若环境不支持会自动降级到无工具模式。

**Q: 如何提升稳定性？**  
A: 固定报告模板、固定评分权重，并在每次输出中写明触发与失效条件。
