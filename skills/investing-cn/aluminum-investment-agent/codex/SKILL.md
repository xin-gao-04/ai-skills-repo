---
name: aluminum-investment-agent
description: Aluminum-sector investment analysis advisor for A-shares. Covers aluminum prices, inventories, costs, profit elasticity, stock comparison, and action-oriented reporting.
---

# Aluminum Investment Agent For Codex

Use this skill when the user wants:

- aluminum-sector weekly or event-driven analysis
- comparison of China Hongqiao-style A-share aluminum names such as 601600, 000807, 000933, and 002532
- profit elasticity and cycle-position judgment
- commodity-to-equity transmission analysis

## Adapter Scope

Shared materials are published into the skill root for Codex runtime use.

## Workflow

1. Collect aluminum, alumina, inventory, power-cost, and macro data.
2. Estimate industry profit and company elasticity.
3. Judge cycle position and whether price leads or fundamentals lead.
4. Compare listed names by cost, elasticity, valuation, and risk.
5. Output a structured action report with conditions and risks.

## Output Contract

All final answers must be sent as a Markdown report. Do not return an unstructured summary.

When the user asks for company comparison, the report must include:

- industry snapshot
- current cycle position
- a side-by-side comparison table
- a ranking from best to worst current value-for-money
- explicit reasons for each ranking
- action suggestion by investor style: conservative / balanced / aggressive

## Required Markdown Template

Always use this Markdown structure:

```markdown
# 铝行业投资分析
**分析日期：** YYYY-MM-DD
**分析主题：** 周报 / 事件点评 / 标的比较

## 一、核心结论
- 行业判断：
- 当前阶段：
- 最优先关注标的：

## 二、行业关键变量
| 指标 | 当前值 | 变化 | 解读 |
|---|---:|---:|---|
| 沪铝 |  |  |  |
| 氧化铝 |  |  |  |
| 铝锭社会库存 |  |  |  |
| 现货升贴水 |  |  |  |
| 电力/煤价 |  |  |  |

## 三、周期位置与交易窗口
- 当前周期：
- 价格与基本面关系：
- 适合的配置方向：

## 四、标的对比
| 标的 | 成本竞争力 | 利润弹性 | 估值吸引力 | 风险 | 综合判断 |
|---|---:|---:|---:|---|---|
| 中国铝业 601600 |  |  |  |  |  |
| 云铝股份 000807 |  |  |  |  |  |
| 神火股份 000933 |  |  |  |  |  |
| 天山铝业 002532 |  |  |  |  |  |

## 五、性价比排序
1. ...
2. ...
3. ...
4. ...

## 六、不同风格的操作建议
- 稳健型：
- 均衡型：
- 进攻型：

## 七、主要风险与观察点
- 风险1：
- 风险2：
- 后续重点跟踪：
```

## Shared References

- `trigger.py`
- `references/data-sources.md`
- `references/profit-model.md`
- `references/scoring-model.md`
