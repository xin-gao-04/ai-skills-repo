"""
A股技术分析数据采集脚本
为 ta-analyst-agent 提供完整的本地数据支持

依赖安装：
    pip install akshare pandas numpy ta-lib-python

用法：
    python fetch_stock_data.py --code 601600 --days 250
    python fetch_stock_data.py --code 601600 --days 250 --output data/601600.json

输出：JSON文件，包含K线、技术指标、情绪数据，直接上传给Claude分析
"""

import json
import argparse
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import akshare as ak
    import pandas as pd
    import numpy as np
except ImportError:
    print("请先安装依赖：pip install akshare pandas numpy")
    exit(1)


# ── 均线计算 ──────────────────────────────────────────────────────────
def calc_ma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean().round(3)


# ── MACD计算 ──────────────────────────────────────────────────────────
def calc_macd(close: pd.Series):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    hist = (dif - dea) * 2
    return dif.round(4), dea.round(4), hist.round(4)


# ── KDJ计算 ──────────────────────────────────────────────────────────
def calc_kdj(high, low, close, n=9):
    low_n = low.rolling(n).min()
    high_n = high.rolling(n).max()
    rsv = (close - low_n) / (high_n - low_n + 1e-10) * 100
    K = rsv.ewm(com=2, adjust=False).mean()
    D = K.ewm(com=2, adjust=False).mean()
    J = 3 * K - 2 * D
    return K.round(2), D.round(2), J.round(2)


# ── RSI计算 ──────────────────────────────────────────────────────────
def calc_rsi(close: pd.Series, period=14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(span=period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(span=period, adjust=False).mean()
    rs = gain / (loss + 1e-10)
    return (100 - 100 / (1 + rs)).round(2)


# ── 布林带计算 ────────────────────────────────────────────────────────
def calc_boll(close: pd.Series, period=20, std_dev=2):
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = (mid + std_dev * std).round(3)
    lower = (mid - std_dev * std).round(3)
    bandwidth = ((upper - lower) / mid * 100).round(2)
    return upper, mid.round(3), lower, bandwidth


# ── ATR计算 ──────────────────────────────────────────────────────────
def calc_atr(high, low, close, period=14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean().round(3)


# ── 斐波那契回撤位 ────────────────────────────────────────────────────
def calc_fibonacci(high: float, low: float) -> dict:
    diff = high - low
    return {
        "high": round(high, 3),
        "0.236": round(high - diff * 0.236, 3),
        "0.382": round(high - diff * 0.382, 3),
        "0.500": round(high - diff * 0.500, 3),
        "0.618": round(high - diff * 0.618, 3),
        "0.786": round(high - diff * 0.786, 3),
        "low":  round(low, 3),
    }


# ── 核心K线数据采集 ──────────────────────────────────────────────────
def fetch_kline(code: str, days: int = 250) -> pd.DataFrame:
    """获取日K线数据"""
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days + 50)).strftime("%Y%m%d")

    # akshare接口：前缀区分沪深
    prefix = "sh" if code.startswith("6") else "sz"
    full_code = f"{prefix}{code}"

    print(f"  正在获取 {full_code} K线数据...")
    df = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start,
        end_date=end,
        adjust="qfq"   # 前复权
    )

    # 统一列名
    df.columns = ["date", "open", "close", "high", "low",
                  "volume", "amount", "amplitude", "pct_change",
                  "change", "turnover"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").tail(days).reset_index(drop=True)
    df["volume"] = df["volume"].astype(float)
    return df


# ── 技术指标计算汇总 ─────────────────────────────────────────────────
def calc_all_indicators(df: pd.DataFrame) -> dict:
    """计算所有技术指标，返回最新值和近期序列"""
    close = df["close"]
    high  = df["high"]
    low   = df["low"]
    vol   = df["volume"]
    n = len(df)

    # 均线
    mas = {f"MA{p}": calc_ma(close, p) for p in [5, 10, 20, 60, 120, 250]}

    # MACD
    dif, dea, hist = calc_macd(close)

    # KDJ
    K, D, J = calc_kdj(high, low, close)

    # RSI
    rsi6  = calc_rsi(close, 6)
    rsi14 = calc_rsi(close, 14)

    # 布林带
    boll_upper, boll_mid, boll_lower, boll_bw = calc_boll(close)

    # ATR
    atr14 = calc_atr(high, low, close, 14)

    # 成交量均线
    vol_ma5  = calc_ma(vol, 5)
    vol_ma20 = calc_ma(vol, 20)

    # 取最新N条用于趋势判断
    recent = 20

    def last(s, n=1):
        """取最后n个非空值"""
        vals = s.dropna().tail(n).tolist()
        return round(vals[-1], 4) if vals else None

    def series_tail(s, n=recent):
        return [round(v, 4) if pd.notna(v) else None for v in s.tail(n).tolist()]

    # 均线多空排列判断
    ma_values = {k: last(v) for k, v in mas.items()}
    valid_mas = {k: v for k, v in ma_values.items() if v is not None}
    sorted_mas = sorted(valid_mas.items(), key=lambda x: int(x[0][2:]))

    ma_alignment = "多头排列"
    for i in range(len(sorted_mas) - 1):
        if sorted_mas[i][1] < sorted_mas[i+1][1]:
            ma_alignment = "空头排列"
            break
    else:
        if len(sorted_mas) < 2:
            ma_alignment = "数据不足"

    # 斐波那契（近250日高低点）
    fib_high = float(high.tail(250).max())
    fib_low  = float(low.tail(250).min())
    fibonacci = calc_fibonacci(fib_high, fib_low)

    # 量价分析（最近5日）
    vol_ratio = float(vol.iloc[-1] / vol_ma20.iloc[-1]) if vol_ma20.iloc[-1] > 0 else 1.0
    price_up = close.iloc[-1] > close.iloc[-2]
    vol_up = vol.iloc[-1] > vol.iloc[-2]

    if price_up and vol_up:
        vol_price_pattern = "量价齐升（健康上涨）"
    elif price_up and not vol_up:
        vol_price_pattern = "价涨量缩（动能减弱）"
    elif not price_up and vol_up:
        vol_price_pattern = "价跌量增（主动抛压）"
    else:
        vol_price_pattern = "价跌量缩（惜售缩量）"

    return {
        "ma_latest": ma_values,
        "ma_alignment": ma_alignment,
        "ma_recent": {k: series_tail(v) for k, v in mas.items()},
        "macd": {
            "dif": last(dif),
            "dea": last(dea),
            "hist": last(hist),
            "dif_above_zero": (last(dif) or 0) > 0,
            "golden_cross_recent": any(
                dif.iloc[i] > dea.iloc[i] and dif.iloc[i-1] <= dea.iloc[i-1]
                for i in range(max(1, n-10), n)
            ),
            "dif_recent":  series_tail(dif),
            "dea_recent":  series_tail(dea),
            "hist_recent": series_tail(hist),
        },
        "kdj": {
            "K": last(K), "D": last(D), "J": last(J),
            "oversold": (last(K) or 50) < 20 and (last(D) or 50) < 20,
            "overbought": (last(K) or 50) > 80 and (last(D) or 50) > 80,
        },
        "rsi": {
            "rsi6":  last(rsi6),
            "rsi14": last(rsi14),
            "above_50": (last(rsi14) or 0) > 50,
        },
        "bollinger": {
            "upper": last(boll_upper),
            "mid":   last(boll_mid),
            "lower": last(boll_lower),
            "bandwidth": last(boll_bw),
            "price_position": (
                "上轨附近" if close.iloc[-1] > (last(boll_upper) or 0) * 0.98
                else "下轨附近" if close.iloc[-1] < (last(boll_lower) or 0) * 1.02
                else "中轨附近" if abs(close.iloc[-1] - (last(boll_mid) or 0)) / (last(boll_mid) or 1) < 0.01
                else "带内运行"
            ),
        },
        "atr14": last(atr14),
        "volume": {
            "latest":         float(vol.iloc[-1]),
            "ma5":            float(vol_ma5.iloc[-1]) if pd.notna(vol_ma5.iloc[-1]) else None,
            "ma20":           float(vol_ma20.iloc[-1]) if pd.notna(vol_ma20.iloc[-1]) else None,
            "ratio_vs_ma20":  round(vol_ratio, 2),
            "vol_price_pattern": vol_price_pattern,
            "recent_turnover": df["turnover"].tail(5).round(2).tolist(),
        },
        "fibonacci": fibonacci,
        "price_structure": {
            "high_250d": round(fib_high, 3),
            "low_250d":  round(fib_low, 3),
            "high_60d":  round(float(high.tail(60).max()), 3),
            "low_60d":   round(float(low.tail(60).min()), 3),
            "high_20d":  round(float(high.tail(20).max()), 3),
            "low_20d":   round(float(low.tail(20).min()), 3),
        }
    }


# ── 情绪数据采集 ──────────────────────────────────────────────────────
def fetch_sentiment(code: str, name: str) -> dict:
    """采集北向资金、融资数据、龙虎榜"""
    sentiment = {}

    # 北向资金持股
    try:
        print("  正在获取北向资金数据...")
        df_north = ak.stock_hsgt_individual_em(symbol=name)
        if df_north is not None and len(df_north) > 0:
            cols = df_north.columns.tolist()
            sentiment["north_bound"] = {
                "available": True,
                "latest_data": df_north.tail(10).to_dict("records"),
                "columns": cols
            }
    except Exception as e:
        sentiment["north_bound"] = {"available": False, "reason": str(e)}

    # 融资余额
    try:
        print("  正在获取融资融券数据...")
        df_margin = ak.stock_margin_detail_em(symbol=code)
        if df_margin is not None and len(df_margin) > 0:
            latest = df_margin.iloc[-1]
            hist = df_margin.tail(20)
            sentiment["margin"] = {
                "available": True,
                "latest": {k: (float(v) if isinstance(v, (int, float, np.number)) else str(v))
                           for k, v in latest.items()},
                "balance_trend": hist.get("融资余额", pd.Series()).tail(10).tolist()
                    if "融资余额" in hist.columns else [],
                "columns": df_margin.columns.tolist()
            }
    except Exception as e:
        sentiment["margin"] = {"available": False, "reason": str(e)}

    # 龙虎榜（近30天）
    try:
        print("  正在获取龙虎榜数据...")
        end_dt = datetime.now().strftime("%Y%m%d")
        start_dt = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        df_lhb = ak.stock_lhb_detail_em(symbol=code, start_date=start_dt, end_date=end_dt)
        if df_lhb is not None and len(df_lhb) > 0:
            sentiment["dragon_tiger"] = {
                "available": True,
                "records": df_lhb.to_dict("records"),
                "count": len(df_lhb)
            }
        else:
            sentiment["dragon_tiger"] = {"available": True, "records": [], "count": 0,
                                          "note": "近30日无上榜记录"}
    except Exception as e:
        sentiment["dragon_tiger"] = {"available": False, "reason": str(e)}

    # 主力资金流向（近10日）
    try:
        print("  正在获取主力资金流向...")
        df_flow = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
        if df_flow is not None and len(df_flow) > 0:
            sentiment["fund_flow"] = {
                "available": True,
                "recent_10d": df_flow.tail(10).to_dict("records"),
                "columns": df_flow.columns.tolist()
            }
    except Exception as e:
        sentiment["fund_flow"] = {"available": False, "reason": str(e)}

    return sentiment


# ── 股票基本信息 ──────────────────────────────────────────────────────
def fetch_basic_info(code: str) -> dict:
    """获取个股基本信息"""
    info = {}
    try:
        df = ak.stock_individual_info_em(symbol=code)
        if df is not None and len(df) > 0:
            info = dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
    except Exception:
        pass
    return info


# ── 主函数 ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="A股技术分析数据采集")
    parser.add_argument("--code",   required=True,  help="股票代码，如 601600")
    parser.add_argument("--days",   default=250,    type=int, help="K线天数（默认250）")
    parser.add_argument("--output", default="",     help="输出JSON文件路径")
    parser.add_argument("--no-sentiment", action="store_true", help="跳过情绪数据（加速）")
    args = parser.parse_args()

    code = args.code.strip().zfill(6)
    print(f"\n{'='*50}")
    print(f"开始采集 {code} 数据...")
    print(f"{'='*50}")

    result = {
        "meta": {
            "code": code,
            "fetch_time": datetime.now().isoformat(),
            "days": args.days,
            "data_source": "akshare (前复权日K线)",
        }
    }

    # 基本信息
    print("\n[1/4] 采集基本信息...")
    result["basic_info"] = fetch_basic_info(code)
    if result["basic_info"]:
        name = result["basic_info"].get("股票简称", code)
        result["meta"]["name"] = name
        print(f"  股票名称: {name}")
    else:
        name = code
        result["meta"]["name"] = code

    # K线与技术指标
    print(f"\n[2/4] 采集 {args.days} 日K线数据...")
    df = fetch_kline(code, args.days)
    result["meta"]["actual_days"] = len(df)
    result["meta"]["date_range"] = {
        "start": str(df["date"].iloc[0].date()),
        "end":   str(df["date"].iloc[-1].date())
    }

    # 最新价格摘要
    latest = df.iloc[-1]
    result["price_summary"] = {
        "date":       str(latest["date"].date()),
        "close":      round(float(latest["close"]), 3),
        "open":       round(float(latest["open"]), 3),
        "high":       round(float(latest["high"]), 3),
        "low":        round(float(latest["low"]), 3),
        "volume":     float(latest["volume"]),
        "amount":     float(latest["amount"]),
        "pct_change": round(float(latest["pct_change"]), 2),
        "turnover":   round(float(latest["turnover"]), 2),
    }

    # 近30日K线明细（给Claude看形态用）
    result["kline_recent_30d"] = []
    for _, row in df.tail(30).iterrows():
        result["kline_recent_30d"].append({
            "date":       str(row["date"].date()),
            "open":       round(float(row["open"]), 3),
            "high":       round(float(row["high"]), 3),
            "low":        round(float(row["low"]), 3),
            "close":      round(float(row["close"]), 3),
            "volume":     float(row["volume"]),
            "pct_change": round(float(row["pct_change"]), 2),
            "turnover":   round(float(row["turnover"]), 2),
        })

    # 技术指标
    print("\n[3/4] 计算技术指标...")
    result["indicators"] = calc_all_indicators(df)
    print("  MACD、KDJ、RSI、布林带、均线系统 ✓")

    # 情绪数据
    if not args.no_sentiment:
        print("\n[4/4] 采集市场情绪数据...")
        result["sentiment"] = fetch_sentiment(code, name)
    else:
        print("\n[4/4] 跳过情绪数据采集")
        result["sentiment"] = {}

    # 输出
    output_path = args.output or f"{code}_ta_data_{datetime.now().strftime('%Y%m%d')}.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ 数据采集完成！")
    print(f"   股票：{name}（{code}）")
    print(f"   最新收盘：{result['price_summary']['close']} 元")
    print(f"   涨跌幅：{result['price_summary']['pct_change']}%")
    print(f"   MA20：{result['indicators']['ma_latest'].get('MA20', 'N/A')}")
    print(f"   MACD DIF：{result['indicators']['macd']['dif']}")
    print(f"   输出文件：{output_path}")
    print(f"\n📋 下一步：将此JSON文件上传给Claude，")
    print(f"   并说：「对{name}进行完整技术分析」")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
