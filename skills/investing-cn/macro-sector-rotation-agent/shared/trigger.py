"""
宏观板块轮动分析 Agent - 定时触发脚本

依赖：
    pip install anthropic schedule python-dotenv

用法：
    python3 trigger.py --run-now
    python3 trigger.py --check-alert
    python3 trigger.py --schedule
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import anthropic


def _build_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 ANTHROPIC_API_KEY，请在 .env 或环境变量中设置。")
    return anthropic.Anthropic(api_key=api_key)


def _extract_text(response) -> str:
    texts = []
    for block in getattr(response, "content", []):
        if getattr(block, "type", "") == "text":
            texts.append(getattr(block, "text", ""))
    return "\n".join(t for t in texts if t).strip()


def _call_model(client, model: str, max_tokens: int, system: str, user_text: str, enable_web_search: bool):
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_text}],
    }
    if enable_web_search:
        payload["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
    try:
        return client.messages.create(**payload)
    except Exception:
        if enable_web_search:
            payload.pop("tools", None)
            return client.messages.create(**payload)
        raise


def load_skill_context(skill_dir: str) -> str:
    """合并 SKILL.md 与 references/*.md 作为 system prompt。"""
    skill_path = Path(skill_dir)
    parts = []

    main_skill = skill_path / "SKILL.md"
    if main_skill.exists():
        parts.append(f"# SKILL INSTRUCTIONS\n\n{main_skill.read_text(encoding='utf-8')}")

    ref_dir = skill_path / "references"
    if ref_dir.exists():
        for ref_file in sorted(ref_dir.glob("*.md")):
            content = ref_file.read_text(encoding="utf-8")
            parts.append(f"# REFERENCE: {ref_file.name}\n\n{content}")

    return "\n\n---\n\n".join(parts)


def run_analysis(
    skill_dir: str,
    output_dir: str = "./reports",
    report_model: str = "claude-opus-4-6",
    enable_web_search: bool = True,
) -> dict:
    """执行一次完整板块轮动分析。"""
    client = _build_client()
    system_prompt = load_skill_context(skill_dir)
    if not system_prompt:
        raise RuntimeError(f"未读取到技能上下文: {skill_dir}")

    today = datetime.now().strftime("%Y年%m月%d日")
    user_message = f"""
请执行今日（{today}）的A股宏观板块轮动分析。

按技能说明中的5个阶段依次完成：
1. 采集宏观、政策、资金、板块表现与国际变量
2. 判断宏观状态与流动性环境
3. 识别板块轮动信号
4. 对主要板块进行打分排序
5. 生成完整周报（含超配/标配/低配建议）

最后输出：
- 完整报告（Markdown）
- 300字内核心摘要
- 未来一周最关键的2个风险点
"""

    response = _call_model(
        client=client,
        model=report_model,
        max_tokens=8000,
        system=system_prompt,
        user_text=user_message,
        enable_web_search=enable_web_search,
    )
    report_content = _extract_text(response)
    if not report_content:
        raise RuntimeError("模型返回为空，未生成报告内容。")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report_file = out / f"macro-sector-weekly-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.md"
    report_file.write_text(report_content, encoding="utf-8")

    summary = report_content[:500] + "..." if len(report_content) > 500 else report_content
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", 0)
    output_tokens = getattr(usage, "output_tokens", 0)
    total_tokens = input_tokens + output_tokens

    return {
        "success": True,
        "report_path": str(report_file),
        "summary": summary,
        "tokens_used": total_tokens,
    }


def check_alert_conditions(
    skill_dir: str,
    alert_model: str = "claude-sonnet-4-6",
    enable_web_search: bool = True,
) -> dict:
    """检查是否有事件触发额外分析。"""
    client = _build_client()
    system_prompt = load_skill_context(skill_dir)

    prompt = """
请快速检查以下板块轮动预警条件（无需完整周报）：
1. 美联储/国内宏观政策是否出现超预期变化？
2. 地缘冲突或贸易摩擦是否显著升级/缓和？
3. 北向资金是否出现单日异常流入/流出？
4. A股风格是否发生明显切换（大盘↔小盘、价值↔成长）？
5. 是否出现单一板块大幅放量并形成扩散迹象？

请用JSON格式回答：
{"alert": true/false, "reasons": ["原因1"], "urgent_level": "high/medium/low"}
"""

    response = _call_model(
        client=client,
        model=alert_model,
        max_tokens=1200,
        system=system_prompt,
        user_text=prompt,
        enable_web_search=enable_web_search,
    )

    text = _extract_text(response)
    if not text:
        return {"alert": False, "reasons": ["模型返回为空"], "urgent_level": "low"}
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            parsed = json.loads(match.group(0))
            return {
                "alert": bool(parsed.get("alert", False)),
                "reasons": parsed.get("reasons", [])[:5],
                "urgent_level": parsed.get("urgent_level", "low"),
            }
    except Exception:
        pass

    return {"alert": False, "reasons": [], "urgent_level": "low"}


def setup_schedule(
    skill_dir: str,
    report_model: str,
    alert_model: str,
    enable_web_search: bool,
):
    """设置定时任务。"""
    try:
        import schedule
        import time
    except ImportError:
        print("请先安装 schedule: pip install schedule")
        return

    def weekly_job():
        try:
            result = run_analysis(
                skill_dir=skill_dir,
                report_model=report_model,
                enable_web_search=enable_web_search,
            )
            print(f"周报完成: {result['report_path']}")
            print(f"Tokens: {result.get('tokens_used', 'N/A')}")
        except Exception as exc:
            print(f"周报任务失败: {exc}")

    def daily_alert_job():
        try:
            result = check_alert_conditions(
                skill_dir=skill_dir,
                alert_model=alert_model,
                enable_web_search=enable_web_search,
            )
            if result.get("alert"):
                print(f"触发预警({result.get('urgent_level', 'unknown')}):")
                for reason in result.get("reasons", []):
                    print(f"- {reason}")
                if result.get("urgent_level") == "high":
                    print("高优先级预警，立即执行完整分析...")
                    run_analysis(
                        skill_dir=skill_dir,
                        report_model=report_model,
                        enable_web_search=enable_web_search,
                    )
        except Exception as exc:
            print(f"预警任务失败: {exc}")

    # 每周日 21:00 周报
    schedule.every().sunday.at("21:00").do(weekly_job)

    # 交易日 14:50 预警检查
    schedule.every().monday.at("14:50").do(daily_alert_job)
    schedule.every().tuesday.at("14:50").do(daily_alert_job)
    schedule.every().wednesday.at("14:50").do(daily_alert_job)
    schedule.every().thursday.at("14:50").do(daily_alert_job)
    schedule.every().friday.at("14:50").do(daily_alert_job)

    print("定时任务已启动: 周日21:00周报, 周一至周五14:50预警检查")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="宏观板块轮动分析 Agent")
    parser.add_argument("--run-now", action="store_true", help="立即执行一次完整分析")
    parser.add_argument("--check-alert", action="store_true", help="仅检查预警条件")
    parser.add_argument("--schedule", action="store_true", help="启动定时任务")
    parser.add_argument(
        "--skill-dir",
        default="./macro-sector-rotation-agent",
        help="SKILL.md 所在目录",
    )
    parser.add_argument("--output-dir", default="./reports", help="报告输出目录")
    parser.add_argument(
        "--report-model",
        default="claude-opus-4-6",
        help="完整报告使用的模型名称",
    )
    parser.add_argument(
        "--alert-model",
        default="claude-sonnet-4-6",
        help="预警检查使用的模型名称",
    )
    parser.add_argument(
        "--disable-web-search",
        action="store_true",
        help="禁用 web_search 工具（环境不支持时可用）",
    )

    args = parser.parse_args()

    if args.run_now:
        try:
            result = run_analysis(
                skill_dir=args.skill_dir,
                output_dir=args.output_dir,
                report_model=args.report_model,
                enable_web_search=not args.disable_web_search,
            )
            print(f"报告路径: {result['report_path']}")
            print(f"摘要预览: {result['summary'][:300]}")
            print(f"总Tokens: {result.get('tokens_used', 'N/A')}")
        except Exception as exc:
            print(f"执行失败: {exc}")
            raise SystemExit(1)
    elif args.check_alert:
        try:
            result = check_alert_conditions(
                skill_dir=args.skill_dir,
                alert_model=args.alert_model,
                enable_web_search=not args.disable_web_search,
            )
            status = "触发" if result.get("alert") else "正常"
            print(f"预警状态: {status}")
            for reason in result.get("reasons", []):
                print(f"- {reason}")
        except Exception as exc:
            print(f"预警检查失败: {exc}")
            raise SystemExit(1)
    elif args.schedule:
        setup_schedule(
            skill_dir=args.skill_dir,
            report_model=args.report_model,
            alert_model=args.alert_model,
            enable_web_search=not args.disable_web_search,
        )
    else:
        parser.print_help()
