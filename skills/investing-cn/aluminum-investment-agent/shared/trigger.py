"""
铝行业投资分析 Agent - 定时触发脚本
配合 cron 或任务调度器使用，自动调用 Claude API 执行周报分析

依赖：
    pip install anthropic schedule python-dotenv

配置：
    创建 .env 文件，填入 ANTHROPIC_API_KEY=sk-ant-xxxx

使用方式：
    手动执行：python trigger.py --run-now
    定时任务：python trigger.py --schedule  (每周五16:30自动执行)
    cron方式：30 16 * * 5 /path/to/python /path/to/trigger.py --run-now
"""

import anthropic
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# ── 读取 SKILL.md 和 references ──────────────────────────────────────
def load_skill_context(skill_dir: str) -> str:
    """将 SKILL.md 和所有 references/*.md 合并为 system prompt"""
    skill_path = Path(skill_dir)
    
    parts = []
    
    # 主 SKILL.md
    main_skill = skill_path / "SKILL.md"
    if main_skill.exists():
        parts.append(f"# SKILL INSTRUCTIONS\n\n{main_skill.read_text(encoding='utf-8')}")
    
    # references 目录
    ref_dir = skill_path / "references"
    if ref_dir.exists():
        for ref_file in sorted(ref_dir.glob("*.md")):
            content = ref_file.read_text(encoding='utf-8')
            parts.append(f"# REFERENCE: {ref_file.name}\n\n{content}")
    
    return "\n\n---\n\n".join(parts)


# ── 核心执行函数 ─────────────────────────────────────────────────────
def run_analysis(skill_dir: str, output_dir: str = "./reports") -> dict:
    """
    执行一次完整的铝行业投资分析
    返回：{"success": bool, "report_path": str, "summary": str}
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # 加载 skill 上下文
    system_prompt = load_skill_context(skill_dir)
    
    # 触发词
    today = datetime.now().strftime("%Y年%m月%d日")
    user_message = f"""
请执行今日（{today}）的铝行业投资分析工作流。

按照技能说明中的5个阶段依次执行：
1. 采集今日价格、库存、成本、宏观数据
2. 测算各标的当前利润弹性
3. 判断当前周期位置
4. 对4个核心标的进行比较评分
5. 生成完整投资周报

最后输出：
- 完整报告（Markdown格式）
- 核心结论摘要（不超过200字）
- 本周最需要关注的1-2个风险点
"""
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始执行分析...")
    
    # 调用 API（使用扩展思考以提高分析质量）
    response = client.messages.create(
        model="claude-opus-4-6",          # 使用最强模型做投研
        max_tokens=8000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    report_content = response.content[0].text
    
    # 保存报告
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"aluminum-weekly-{datetime.now().strftime('%Y-%m-%d')}.md"
    report_file = output_path / filename
    report_file.write_text(report_content, encoding='utf-8')
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 分析完成，报告已保存：{report_file}")
    
    # 提取摘要（取报告前500字作为预览）
    summary_preview = report_content[:500] + "..." if len(report_content) > 500 else report_content
    
    return {
        "success": True,
        "report_path": str(report_file),
        "summary": summary_preview,
        "tokens_used": response.usage.input_tokens + response.usage.output_tokens
    }


# ── 预警触发函数 ─────────────────────────────────────────────────────
def check_alert_conditions(skill_dir: str) -> dict:
    """
    快速检查是否触发预警条件（不跑完整分析，只看关键指标）
    返回：{"alert": bool, "reasons": list}
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    system_prompt = load_skill_context(skill_dir)
    
    alert_check_prompt = """
请快速检查以下铝市预警条件是否触发（只需搜索必要数据，不需要完整分析）：

预警触发条件（任一满足即报警）：
1. 沪铝期货单日涨跌幅是否超过3%？
2. 本周铝锭社会库存变化是否超过±10万吨？
3. 氧化铝价格本周涨跌是否超过5%？
4. 云南是否出现新的限电减产公告？
5. 美联储或重大宏观事件是否有超预期表态？

请搜索最新数据后，用JSON格式回答：
{"alert": true/false, "reasons": ["触发原因1", "触发原因2"], "urgent_level": "high/medium/low"}
"""
    
    response = client.messages.create(
        model="claude-sonnet-4-6",        # 预警检查用较快的模型
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": alert_check_prompt}]
    )
    
    try:
        # 尝试解析JSON
        text = response.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    
    return {"alert": False, "reasons": [], "urgent_level": "low"}


# ── 定时调度 ─────────────────────────────────────────────────────────
def setup_schedule(skill_dir: str):
    """设置定时任务"""
    try:
        import schedule
        import time
    except ImportError:
        print("请先安装 schedule: pip install schedule")
        return
    
    def weekly_job():
        print(f"\n{'='*50}")
        print(f"触发周报分析：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        result = run_analysis(skill_dir)
        print(f"报告路径：{result['report_path']}")
        print(f"消耗Tokens：{result.get('tokens_used', 'N/A')}")
    
    def daily_alert_check():
        result = check_alert_conditions(skill_dir)
        if result.get("alert"):
            print(f"\n⚠️  预警触发！紧急程度：{result.get('urgent_level', 'unknown')}")
            for reason in result.get("reasons", []):
                print(f"   - {reason}")
            # 如果是高紧急度，立即执行完整分析
            if result.get("urgent_level") == "high":
                print("触发高紧急度预警，立即执行完整分析...")
                run_analysis(skill_dir)
    
    # 每周五16:30执行完整周报
    schedule.every().friday.at("16:30").do(weekly_job)
    
    # 每个交易日15:30检查预警条件（收盘后）
    schedule.every().monday.at("15:30").do(daily_alert_check)
    schedule.every().tuesday.at("15:30").do(daily_alert_check)
    schedule.every().wednesday.at("15:30").do(daily_alert_check)
    schedule.every().thursday.at("15:30").do(daily_alert_check)
    schedule.every().friday.at("15:30").do(daily_alert_check)
    
    print("定时任务已设置：")
    print("  - 每周五 16:30 执行完整铝市周报")
    print("  - 周一至周五 15:30 检查预警条件")
    print("按 Ctrl+C 停止\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


# ── 命令行入口 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="铝行业投资分析 Agent")
    parser.add_argument("--run-now", action="store_true", help="立即执行一次完整分析")
    parser.add_argument("--check-alert", action="store_true", help="检查预警条件")
    parser.add_argument("--schedule", action="store_true", help="启动定时任务模式")
    parser.add_argument("--skill-dir", default="./aluminum-investment-agent", 
                       help="SKILL.md 所在目录路径")
    parser.add_argument("--output-dir", default="./reports", help="报告输出目录")
    
    args = parser.parse_args()
    
    if args.run_now:
        result = run_analysis(args.skill_dir, args.output_dir)
        print(f"\n报告路径：{result['report_path']}")
        print(f"\n摘要预览：\n{result['summary'][:300]}")
    
    elif args.check_alert:
        result = check_alert_conditions(args.skill_dir)
        print(f"预警状态：{'⚠️ 触发' if result.get('alert') else '✅ 正常'}")
        if result.get("reasons"):
            for r in result["reasons"]:
                print(f"  - {r}")
    
    elif args.schedule:
        setup_schedule(args.skill_dir)
    
    else:
        parser.print_help()
