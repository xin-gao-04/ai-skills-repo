---
name: stock-technical-trade-advisor
description: Technical analysis and trade-action advisor for a single stock or ETF. Uses shared/analyze_stock.py and returns structured trading guidance with position-aware scenarios.
---

# Stock Technical Trade Advisor For Codex

Use this skill when the user wants technical analysis or trade-action guidance for a single stock or ETF.

## Adapter Scope

This file is the Codex-specific adapter. At publish time, shared assets are copied into the skill root.

## Before Running

If the user only provides a symbol or says "analyze this stock", ask the minimum required context first:

- Are they `holding`, `watching`, or `preparing to buy`?
- If holding: what is the cost basis and share count?
- Are they trading `short-term`, `swing`, or `position`?

If the user says not to ask follow-up questions, use defaults:

- `position-status`: `watch`
- `risk-style`: `balanced`
- `horizon`: `swing`

## Shared Commands

Run from this skill directory or adapt the path explicitly:

```bash
pip install -r requirements.txt
python analyze_stock.py --symbol 600584 --market cn
```

For richer A-share review data before a Claude-side or manual deep dive:

```bash
python fetch_stock_data.py --code 601600 --days 250
```

## Position-Aware Run

```bash
python analyze_stock.py --symbol 600584 --market cn --position-status holding --cost-price 45.8 --shares 2000 --risk-style balanced --horizon swing --no-interactive
```

## Output Requirements

Your response must be sent as a complete Markdown report. Do not answer in plain prose-only form.

Your response must distinguish:

- generic technical conclusion
- position-aware conclusion
- condition-triggered action plan

Reasoning must explicitly cover:

1. current structure across month, week, and day: strong trend, weak repair, range, or medium-term weakening
2. bullish evidence versus bearish evidence
3. signal conflict and why key levels matter
4. portfolio action after applying cost basis, size, and risk style
5. three scenarios: strong repair, neutral range, continued weakening
6. when available, how sentiment clues such as northbound flow, margin data, or dragon-tiger records change confidence

## Required Markdown Template

Always use this Markdown structure:

```markdown
# [股票名称/ETF名称] 技术交易分析
**分析日期：** YYYY-MM-DD
**标的：** [代码]
**交易视角：** 短线 / 波段 / 中期
**持仓状态：** 持有 / 观察 / 准备买入

## 一、核心结论
- 结构判断：
- 当前建议：
- 最关键风险：

## 二、多周期结构
- 月线：
- 周线：
- 日线：
- 三周期共振：

## 三、多头与空头证据
### 多头证据
- ...

### 空头证据
- ...

## 四、关键价位
- 强支撑：
- 次支撑：
- 当前价：
- 第一压力：
- 第二压力：

## 五、仓位与动作建议
- 当前动作：
- 参考仓位：
- 止损条件：
- 止盈/减仓条件：

## 六、情景推演
### 情景A：强修复
- 触发条件：
- 应对动作：

### 情景B：中性震荡
- 触发条件：
- 应对动作：

### 情景C：继续走弱
- 触发条件：
- 应对动作：

## 七、补充观察项
- 北向资金/融资/龙虎榜：
- 后续要验证的数据：
```

## Reference Files

- `analyze_stock.py`
- `fetch_stock_data.py`
- `example_output.md`
- `requirements.txt`
- `references/indicators.md`
- `references/risk-management.md`
- `references/sentiment.md`
