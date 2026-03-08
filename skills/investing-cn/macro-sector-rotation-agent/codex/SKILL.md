---
name: macro-sector-rotation-agent
description: A-share macro regime and sector rotation advisor. Produces sector ranking, style rotation judgment, and structured allocation guidance using the shared reference framework.
---

# Macro Sector Rotation Agent For Codex

Use this skill when the user wants:

- A-share sector rotation analysis
- weekly or monthly allocation views
- style switching judgment across value, growth, and defense
- macro or policy-driven sector recommendations

## Adapter Scope

Shared materials are published into the skill root for Codex runtime use.

## Workflow

1. Build a macro snapshot: PMI, social financing, CPI/PPI, rates, DXY, policy headlines.
2. Judge macro regime and liquidity state.
3. Score sector signals across momentum, valuation, fundamentals, and catalysts.
4. Rank sectors and output overweights, neutral allocations, and avoids.
5. Explicitly resolve signal conflicts.

## Output Contract

All final answers must be sent as a Markdown report. Do not return a short plain summary.

The report must move from macro judgment to actionable sector selection. In addition to sector ranking, you must include:

- leading sectors worth prioritizing now
- for each leading sector, 2-4 representative A-share names worth tracking
- for each name, a brief reason it represents the sector logic
- the condition under which the sector thesis is confirmed or invalidated

Do not stop at sector names alone. The report should help portfolio construction.

## Required Markdown Template

Always use this Markdown structure:

```markdown
# A股宏观板块轮动分析
**分析日期：** YYYY-MM-DD
**分析类型：** 周报 / 月报 / 事件点评

## 一、核心结论
- 宏观状态：
- 流动性状态：
- 当前主线板块：
- 当前应回避方向：

## 二、宏观与流动性环境
- 增长：
- 通胀：
- 利率与汇率：
- 政策主线：
- 外部风险：

## 三、风格判断
- 大盘价值 / 小盘成长 / 红利防御 / 均衡
- 理由：

## 四、板块排序
| 板块 | 综合得分 | 当前评级 | 主逻辑 | 主要风险 | 观察周期 |
|---|---:|---|---|---|---|
|  |  |  |  |  |  |

## 五、龙头板块与关注标的
### 1. [板块名称]
- 板块逻辑：
- 确认信号：
- 失效信号：

| 标的 | 代码 | 关注理由 | 更适合的角色 |
|---|---|---|---|
|  |  |  | 龙头 / 弹性 / 防御 |

### 2. [板块名称]
- 板块逻辑：
- 确认信号：
- 失效信号：

| 标的 | 代码 | 关注理由 | 更适合的角色 |
|---|---|---|---|
|  |  |  | 龙头 / 弹性 / 防御 |

## 六、配置建议
- 超配：
- 中性：
- 回避：

## 七、冲突信号裁决
- 冲突类型：
- 当前采用判断：
- 切换阈值：

## 八、后续观察清单
- 数据验证点：
- 板块轮动触发点：
- 风险提示：
```

## Shared References

- `trigger.py`
- `references/data-sources.md`
- `references/regime-sector-playbook.md`
- `references/rotation-signal-model.md`
- `references/sector-scoring-model.md`
- `references/quality-checklist.md`
