import argparse
import contextlib
import json
import math
import os
from io import StringIO
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

DEFAULT_WEIGHTS: Dict[str, float] = {
    "ma_stack": 8,
    "price_above_ma20": 7,
    "price_above_ma60": 5,
    "ma20_slope": 5,
    "ma60_slope": 4,
    "ret20": 5,
    "ret60": 4,
    "drawdown_from_high120": 3,
    "anchor_breakout_strength": 9,
    "pullback_depth": 10,
    "pullback_volume_shrink": 10,
    "pullback_days": 4,
    "distribution_risk": 8,
    "rsi14": 4,
    "macd_hist": 5,
    "adx14": 4,
    "mfi14": 3,
    "stochastic_kd": 2,
    "cci20": 2,
    "bollinger_pos": 3,
    "atr20_pct": 3,
    "obv_slope": 2,
    "close_in_day_range": 2,
    "upper_shadow_risk": 3,
    "relative_strength_20": 8,
    "bench_trend": 4,
}


@dataclass
class UserProfile:
    position_status: str = "unknown"
    cost_price: Optional[float] = None
    shares: Optional[int] = None
    risk_style: str = "balanced"
    horizon: str = "swing"
    max_drawdown_pct: Optional[float] = None


def classify_trend_from_frame(df: pd.DataFrame, short_ma: int, long_ma: int) -> str:
    frame = df.copy()
    frame["MA_SHORT"] = frame["Close"].rolling(short_ma).mean()
    frame["MA_LONG"] = frame["Close"].rolling(long_ma).mean()
    if len(frame) < long_ma or pd.isna(frame["MA_LONG"].iloc[-1]):
        return "数据不足"
    last = frame.iloc[-1]
    prev_short = frame["MA_SHORT"].iloc[-min(3, len(frame))]
    slope_up = pd.notna(prev_short) and last["MA_SHORT"] >= prev_short
    if last["Close"] >= last["MA_SHORT"] >= last["MA_LONG"] and slope_up:
        return "上升趋势"
    if last["Close"] >= last["MA_LONG"] and slope_up:
        return "弱修复"
    if last["Close"] < last["MA_SHORT"] < last["MA_LONG"]:
        return "下降趋势"
    return "震荡整理"


def build_multi_timeframe_view(df: pd.DataFrame) -> Dict[str, object]:
    daily = classify_trend_from_frame(df, 20, 60)
    weekly_df = (
        df[["Open", "High", "Low", "Close", "Volume"]]
        .resample("W-FRI")
        .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
        .dropna()
    )
    monthly_df = (
        df[["Open", "High", "Low", "Close", "Volume"]]
        .resample("ME")
        .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
        .dropna()
    )
    weekly = classify_trend_from_frame(weekly_df, 4, 10) if len(weekly_df) >= 10 else "数据不足"
    monthly = classify_trend_from_frame(monthly_df, 3, 6) if len(monthly_df) >= 6 else "数据不足"

    direction_map = {"上升趋势": 1, "弱修复": 1, "震荡整理": 0, "下降趋势": -1}
    daily_sign = direction_map.get(daily, 0)
    weekly_sign = direction_map.get(weekly, 0)
    monthly_sign = direction_map.get(monthly, 0)
    non_zero = [x for x in [daily_sign, weekly_sign, monthly_sign] if x != 0]
    consistency_score = 0
    if non_zero:
        head = non_zero[0]
        consistency_score = sum(1 for x in [daily_sign, weekly_sign, monthly_sign] if x == head and x != 0)

    return {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "consistency_score": consistency_score,
    }


def suggested_position_band(score: float, risk_style: str) -> Tuple[str, str]:
    if score >= 85:
        base = ("30-40%", "70%")
    elif score >= 70:
        base = ("20-30%", "50%")
    elif score >= 55:
        base = ("10-20%", "30%")
    elif score >= 40:
        base = ("0-10%", "10%")
    else:
        base = ("0%", "0%")

    if risk_style == "conservative":
        mapping = {
            "30-40%": "20-30%",
            "20-30%": "10-20%",
            "10-20%": "5-10%",
            "0-10%": "0-5%",
        }
        return mapping.get(base[0], base[0]), base[1]
    if risk_style == "aggressive":
        mapping = {
            "20-30%": "25-35%",
            "10-20%": "15-25%",
            "0-10%": "5-15%",
        }
        return mapping.get(base[0], base[0]), base[1]
    return base


def safe_series(df: pd.DataFrame, col: str) -> Optional[pd.Series]:
    return df[col] if col in df.columns else None


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, adjust=False).mean()
    ma_down = down.ewm(alpha=1 / period, adjust=False).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    fast = ema(series, 12)
    slow = ema(series, 26)
    line = fast - slow
    signal = ema(line, 9)
    hist = line - signal
    return line, signal, hist


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    return true_range(df).rolling(period).mean()


def bollinger_pos(series: pd.Series, period: int = 20) -> pd.Series:
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = mid + 2 * std
    lower = mid - 2 * std
    width = (upper - lower).replace(0, np.nan)
    return (series - lower) / width


def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["Close"].diff().fillna(0))
    return (direction * df["Volume"].fillna(0)).cumsum()


def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    mf = tp * df["Volume"]
    pos = mf.where(tp.diff() > 0, 0.0)
    neg = mf.where(tp.diff() < 0, 0.0)
    pos_sum = pos.rolling(period).sum()
    neg_sum = neg.abs().rolling(period).sum().replace(0, np.nan)
    ratio = pos_sum / neg_sum
    return 100 - (100 / (1 + ratio))


def stochastic_kd(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series]:
    low_n = df["Low"].rolling(period).min()
    high_n = df["High"].rolling(period).max()
    k = 100 * (df["Close"] - low_n) / (high_n - low_n).replace(0, np.nan)
    d = k.rolling(3).mean()
    return k, d


def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    sma_tp = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - sma_tp) / (0.015 * mad.replace(0, np.nan))


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    up_move = df["High"].diff()
    down_move = -df["Low"].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = true_range(df)
    atr_n = tr.rolling(period).mean().replace(0, np.nan)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).sum() / atr_n
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).sum() / atr_n
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    return dx.rolling(period).mean()


@contextlib.contextmanager
def cleared_proxy_env():
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"]
    original = {key: os.environ.get(key) for key in proxy_keys}
    try:
        for key in proxy_keys:
            os.environ.pop(key, None)
        os.environ["NO_PROXY"] = "*"
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    mapper = {}
    alias_map = {
        "open": "Open",
        "开盘": "Open",
        "high": "High",
        "最高": "High",
        "low": "Low",
        "最低": "Low",
        "close": "Close",
        "收盘": "Close",
        "adj close": "Close",
        "volume": "Volume",
        "成交量": "Volume",
        "vol": "Volume",
        "date": "Date",
        "日期": "Date",
        "datetime": "Date",
    }
    for c in df.columns:
        lc = c.lower()
        if lc in alias_map:
            mapper[c] = alias_map[lc]
    df = df.rename(columns=mapper)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").set_index("Date")
    else:
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
    needed = ["Open", "High", "Low", "Close", "Volume"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"missing required column: {col}")
    return df[needed].dropna()


def fetch_cn_data_with_akshare(symbol: str) -> pd.DataFrame:
    import akshare as ak

    fetchers = [
        lambda: ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq"),
        lambda: ak.fund_etf_hist_em(symbol=symbol, period="daily", adjust="qfq"),
    ]
    errors: List[str] = []
    with cleared_proxy_env():
        for fetcher in fetchers:
            try:
                raw = fetcher()
                if raw is not None and len(raw) > 0:
                    return normalize_columns(raw)
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
    joined = "; ".join(errors) if errors else "no data returned"
    raise RuntimeError(f"akshare failed: {joined}")


def cn_exchange_prefix(symbol: str) -> str:
    return "sh" if symbol.startswith(("5", "6", "9")) else "sz"


def fetch_cn_data_with_tencent(symbol: str) -> pd.DataFrame:
    import requests

    secid = f"{cn_exchange_prefix(symbol)}{symbol}"
    session = requests.Session()
    session.trust_env = False
    response = session.get(
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
        params={"param": f"{secid},day,,,320,qfq"},
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data", {}).get(secid, {})
    rows = data.get("qfqday") or data.get("day") or []
    if not rows:
        raise RuntimeError("empty response")
    normalized_rows = [row[:6] for row in rows]
    df = pd.DataFrame(normalized_rows, columns=["Date", "Open", "Close", "High", "Low", "Volume"])
    for col in ["Open", "Close", "High", "Low", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return normalize_columns(df)


def fetch_with_yfinance(ticker_symbol: str) -> pd.DataFrame:
    import yfinance as yf

    with cleared_proxy_env():
        ticker = yf.Ticker(ticker_symbol)
        raw = ticker.history(period="2y", auto_adjust=True)
    if raw is None or len(raw) == 0:
        raise RuntimeError("empty response")
    return normalize_columns(raw.reset_index())


def fetch_with_stooq(symbol: str) -> pd.DataFrame:
    import requests

    stooq_symbol = symbol.lower()
    if "." not in stooq_symbol:
        stooq_symbol = f"{stooq_symbol}.us"

    session = requests.Session()
    session.trust_env = False
    response = session.get(
        "https://stooq.com/q/d/l/",
        params={"s": stooq_symbol, "i": "d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    text = response.text.strip()
    if not text or text.lower().startswith("no data"):
        raise RuntimeError("empty response")
    return normalize_columns(pd.read_csv(StringIO(text)))


def fetch_data(symbol: str, market: str) -> pd.DataFrame:
    market = market.lower()
    if market == "cn":
        errors: List[str] = []
        try:
            return fetch_cn_data_with_akshare(symbol)
        except Exception as e:
            errors.append(str(e))
        try:
            return fetch_cn_data_with_tencent(symbol)
        except Exception as e:
            errors.append(f"tencent failed: {e}")
        try:
            suffix = ".SS" if symbol.startswith("6") else ".SZ"
            return fetch_with_yfinance(f"{symbol}{suffix}")
        except Exception as e:
            errors.append(f"yfinance failed: {e}")
        raise RuntimeError("failed to fetch CN data: " + " | ".join(errors))
    else:
        errors: List[str] = []
        try:
            return fetch_with_yfinance(symbol)
        except Exception as e:
            errors.append(f"yfinance failed: {e}")
        try:
            return fetch_with_stooq(symbol)
        except Exception as e:
            errors.append(f"stooq failed: {e}")
        raise RuntimeError(f"failed to fetch US data: {' | '.join(errors)}")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for n in [5, 10, 20, 60, 120]:
        df[f"MA{n}"] = sma(df["Close"], n)
    df["RET20"] = df["Close"].pct_change(20)
    df["RET60"] = df["Close"].pct_change(60)
    df["HIGH120"] = df["Close"].rolling(120).max()
    df["DD120"] = df["Close"] / df["HIGH120"] - 1
    df["VOL_MA20"] = sma(df["Volume"], 20)
    df["VOL_RATIO"] = df["Volume"] / df["VOL_MA20"].replace(0, np.nan)
    df["RSI14"] = rsi(df["Close"], 14)
    macd_line, macd_signal, macd_hist = macd(df["Close"])
    df["MACD"] = macd_line
    df["MACD_SIGNAL"] = macd_signal
    df["MACD_HIST"] = macd_hist
    df["ATR14"] = atr(df, 14)
    df["ATR20"] = atr(df, 20)
    df["ATR20_PCT"] = df["ATR20"] / df["Close"]
    df["BOLL_POS"] = bollinger_pos(df["Close"], 20)
    df["OBV"] = obv(df)
    df["OBV_SLOPE5"] = df["OBV"].diff(5)
    df["MFI14"] = mfi(df, 14)
    k, d = stochastic_kd(df, 14)
    df["K14"] = k
    df["D14"] = d
    df["CCI20"] = cci(df, 20)
    df["ADX14"] = adx(df, 14)
    day_range = (df["High"] - df["Low"]).replace(0, np.nan)
    df["CLOSE_IN_DAY_RANGE"] = (df["Close"] - df["Low"]) / day_range
    upper_shadow = df["High"] - df[["Open", "Close"]].max(axis=1)
    body = (df["Close"] - df["Open"]).abs().replace(0, np.nan)
    df["UPPER_SHADOW_RATIO"] = upper_shadow / body
    df["MA20_SLOPE5"] = df["MA20"].diff(5)
    df["MA60_SLOPE5"] = df["MA60"].diff(5)
    return df


def find_anchor(df: pd.DataFrame, lookback: int = 30) -> Optional[pd.Timestamp]:
    tail = df.tail(lookback).copy()
    cond = (
        (tail["Close"].pct_change() > 0.03)
        & (tail["VOL_RATIO"] > 1.5)
        & (tail["Close"] >= tail["Close"].rolling(20).max().shift(1).fillna(-np.inf))
    )
    candidates = tail.index[cond.fillna(False)]
    if len(candidates) == 0:
        return None
    return candidates[-1]


def maybe(value, fn):
    try:
        if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
            return None
        return fn(value)
    except Exception:
        return None


def round_price(value: Optional[float]) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)


def prompt_text(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else (default or "")


def prompt_float(prompt: str) -> Optional[float]:
    value = input(f"{prompt}: ").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def prompt_int(prompt: str) -> Optional[int]:
    value = input(f"{prompt}: ").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def collect_user_profile(args) -> UserProfile:
    if args.no_interactive:
        return UserProfile(
            position_status=args.position_status or "unknown",
            cost_price=args.cost_price,
            shares=args.shares,
            risk_style=args.risk_style,
            horizon=args.horizon,
            max_drawdown_pct=args.max_drawdown_pct,
        )

    position_status = args.position_status or prompt_text("当前状态（flat/holding/watch）", "watch").lower()
    cost_price = args.cost_price
    shares = args.shares
    if position_status == "holding":
        if cost_price is None:
            cost_price = prompt_float("请输入持仓成本价")
        if shares is None:
            shares = prompt_int("请输入持仓股数")
    risk_style = args.risk_style or prompt_text("风险偏好（conservative/balanced/aggressive）", "balanced").lower()
    horizon = args.horizon or prompt_text("计划周期（short/swing/position）", "swing").lower()
    max_drawdown_pct = args.max_drawdown_pct
    if max_drawdown_pct is None:
        max_drawdown_pct = prompt_float("你能接受的最大亏损百分比（可留空）")
    return UserProfile(
        position_status=position_status,
        cost_price=cost_price,
        shares=shares,
        risk_style=risk_style,
        horizon=horizon,
        max_drawdown_pct=max_drawdown_pct,
    )


def score_indicator(results: Dict[str, Optional[float]], weights: Dict[str, float]) -> Tuple[float, float, List[str]]:
    score_sum = 0.0
    weight_sum = 0.0
    skipped = []
    for name, weight in weights.items():
        val = results.get(name)
        if val is None:
            skipped.append(name)
            continue
        score_sum += max(0.0, min(1.0, float(val))) * weight
        weight_sum += weight
    final_score = 100.0 * score_sum / weight_sum if weight_sum > 0 else 0.0
    return final_score, weight_sum, skipped


def build_interaction_prompts(symbol: str, profile: Optional[UserProfile], analysis_mode: str) -> Dict:
    profile = profile or UserProfile()
    missing: List[str] = []
    if profile.position_status in ["unknown", ""]:
        missing.append("position_status")
    if profile.position_status == "holding":
        if profile.cost_price is None:
            missing.append("cost_price")
        if profile.shares is None:
            missing.append("shares")
    if not profile.horizon:
        missing.append("horizon")

    first_round = [
        f"{symbol} 你现在是持仓中、空仓观察，还是准备买入？",
        "如果持仓中：成本价和股数是多少？",
        "你这笔更偏短线、波段，还是偏长持有？",
    ]
    second_round = [
        "你能接受的最大亏损大概是多少百分比？",
        "是否需要加入基准指数一起比较强弱？",
    ]
    mode_hint = {
        "premarket": "盘前模式下，优先确认今天关注的是高开承接、低开防守还是突破预案。",
        "intraday": "盘中模式下，优先确认当下是否已有仓位，以及是否需要追踪分时突破与回落承接。",
        "close": "收盘模式下，优先确认今天收盘后的仓位处理和次日计划。",
    }.get(analysis_mode, "")
    return {
        "missing_fields": missing,
        "first_round_questions": first_round,
        "second_round_questions": second_round,
        "mode_hint": mode_hint,
    }


def build_trade_plan(
    result: Dict,
    df: pd.DataFrame,
    bench_df: Optional[pd.DataFrame],
    profile: Optional[UserProfile],
) -> Dict:
    last = df.iloc[-1]
    current = float(last["Close"])
    ma5 = float(last["MA5"]) if pd.notna(last.get("MA5")) else current
    ma10 = float(last["MA10"]) if pd.notna(last.get("MA10")) else current
    ma20 = float(last["MA20"]) if pd.notna(last.get("MA20")) else current
    ma60 = float(last["MA60"]) if pd.notna(last.get("MA60")) else current
    atr20 = float(last["ATR20"]) if pd.notna(last.get("ATR20")) else max(current * 0.03, 0.01)
    recent_high_20 = float(df["High"].tail(20).max())
    recent_low_10 = float(df["Low"].tail(10).min())
    recent_low_20 = float(df["Low"].tail(20).min())
    breakout_buy = max(recent_high_20 * 1.005, current + 0.5 * atr20)
    pullback_buy = max(ma20, recent_low_10)
    defensive_stop = min(ma60, recent_low_20, ma20 - 1.2 * atr20)
    risk_stop = min(recent_low_10, current - 2.0 * atr20)
    stop_price = max(min(defensive_stop, current * 0.98), risk_stop)
    take_profit_1 = current + 1.5 * atr20
    take_profit_2 = max(recent_high_20 * 1.06, current + 3.0 * atr20)
    entry_low = min(pullback_buy, current)
    entry_high = max(current, breakout_buy)

    profile = profile or UserProfile()
    actions: List[str] = []
    buy_conditions: List[str] = []
    sell_conditions: List[str] = []
    entry_reference = pullback_buy if result["classification"] in ["趋势延续型", "试盘整理型"] else current
    risk_pct = max((entry_reference - stop_price) / max(entry_reference, 0.01) * 100, 0.1)
    reward_pct_1 = max((take_profit_1 - entry_reference) / max(entry_reference, 0.01) * 100, 0.0)
    reward_pct_2 = max((take_profit_2 - entry_reference) / max(entry_reference, 0.01) * 100, 0.0)
    rr1 = reward_pct_1 / risk_pct if risk_pct > 0 else None
    rr2 = reward_pct_2 / risk_pct if risk_pct > 0 else None
    initial_position, max_position = suggested_position_band(result["score"], profile.risk_style)

    if result["classification"] == "趋势延续型":
        buy_conditions.append(f"放量站上 {round_price(breakout_buy)} 可考虑试仓，优先分两笔介入。")
        buy_conditions.append(f"回踩 {round_price(pullback_buy)} 附近缩量企稳，可考虑低吸而不是追高。")
        sell_conditions.append(f"日线收盘跌破 {round_price(stop_price)}，视为结构转弱，优先执行止损或大幅减仓。")
        sell_conditions.append(f"冲高至 {round_price(take_profit_1)} 至 {round_price(take_profit_2)} 区间若放量滞涨，可分批兑现。")
    elif result["classification"] == "试盘整理型":
        buy_conditions.append(f"只有重新放量突破 {round_price(breakout_buy)} 才考虑开仓，否则继续等待。")
        sell_conditions.append(f"若跌破 {round_price(stop_price)}，说明试盘失败，应回避或减仓。")
    elif result["classification"] == "弱反弹型":
        buy_conditions.append(f"仅在收复 {round_price(ma20)} 且量能回升时考虑轻仓试错。")
        sell_conditions.append(f"跌破 {round_price(stop_price)} 或反弹到 {round_price(ma20)} 附近无量受阻，应降低预期。")
    else:
        buy_conditions.append("当前不适合主动追买，优先等更清晰的量价确认。")
        sell_conditions.append(f"若跌破 {round_price(stop_price)}，弱势结构大概率延续。")

    if profile.position_status == "holding":
        if profile.cost_price is not None:
            pnl_pct = (current / profile.cost_price - 1.0) * 100
            actions.append(f"按当前收盘价估算，持仓浮动收益约 {round(pnl_pct, 2)}%。")
        actions.append(f"持仓处理上，先看 {round_price(ma20)} 是否继续守住；失守且次日不能收回，建议先减仓。")
        actions.append(f"若放量突破 {round_price(breakout_buy)}，可考虑保留核心仓，分批上移止盈位到 {round_price(ma20)} 上方。")
    elif profile.position_status in ["flat", "watch"]:
        actions.append("当前更适合按触发条件执行，不建议无条件追价。")
        actions.append(f"首选方案是等突破价 {round_price(breakout_buy)} 被确认，次选方案是等回踩 {round_price(pullback_buy)} 缩量企稳。")
    else:
        actions.append("未提供持仓状态，以下建议按通用观察清单理解。")

    if profile.risk_style == "conservative":
        actions.append("风险偏好偏保守时，优先只做右侧突破确认，不做盘中抢反弹。")
        stop_price = max(stop_price, ma20 - 0.8 * atr20)
    elif profile.risk_style == "aggressive":
        actions.append("风险偏好偏进取时，可接受更早试仓，但单次仓位仍建议受控。")

    if profile.horizon == "short":
        actions.append("短线视角下，量能和次日承接优先级高于均线斜率。")
    elif profile.horizon == "position":
        actions.append("波段偏长时，更关注 MA20/MA60 的趋势连续性，不必过度响应单日波动。")

    actions.append(f"参考入场区间可先看 {round_price(entry_low)} 到 {round_price(entry_high)}，不要把突破买点和回踩买点混成同一笔。")
    actions.append(f"初始仓位可参考 {initial_position}，最大仓位上限参考 {max_position}。")

    levels = {
        "current_close": round_price(current),
        "ma5": round_price(ma5),
        "ma10": round_price(ma10),
        "ma20": round_price(ma20),
        "ma60": round_price(ma60),
        "atr20": round_price(atr20),
        "recent_high_20": round_price(recent_high_20),
        "recent_low_10": round_price(recent_low_10),
        "recent_low_20": round_price(recent_low_20),
        "breakout_buy": round_price(breakout_buy),
        "pullback_buy": round_price(pullback_buy),
        "entry_range_low": round_price(entry_low),
        "entry_range_high": round_price(entry_high),
        "stop_price": round_price(stop_price),
        "take_profit_1": round_price(take_profit_1),
        "take_profit_2": round_price(take_profit_2),
    }
    if bench_df is not None and len(bench_df) > 0:
        bench_last = bench_df.iloc[-1]
        levels["bench_close"] = round_price(float(bench_last["Close"]))

    return {
        "actions": actions,
        "buy_conditions": buy_conditions,
        "sell_conditions": sell_conditions,
        "levels": levels,
        "position_plan": {
            "initial_position": initial_position,
            "max_position": max_position,
        },
        "risk_reward": {
            "risk_pct": round(risk_pct, 2),
            "reward_pct_1": round(reward_pct_1, 2),
            "reward_pct_2": round(reward_pct_2, 2),
            "ratio_1": round(rr1, 2) if rr1 is not None else None,
            "ratio_2": round(rr2, 2) if rr2 is not None else None,
        },
    }


def build_reasoning(
    result: Dict,
    df: pd.DataFrame,
    bench_df: Optional[pd.DataFrame],
    profile: Optional[UserProfile],
    analysis_mode: str,
) -> Dict:
    last = df.iloc[-1]
    current = float(last["Close"])
    ma20 = float(last["MA20"]) if pd.notna(last.get("MA20")) else current
    ma60 = float(last["MA60"]) if pd.notna(last.get("MA60")) else current
    ret20 = float(last["RET20"]) if pd.notna(last.get("RET20")) else None
    macd_hist = float(last["MACD_HIST"]) if pd.notna(last.get("MACD_HIST")) else None
    adx14 = float(last["ADX14"]) if pd.notna(last.get("ADX14")) else None
    vol_ratio = float(last["VOL_RATIO"]) if pd.notna(last.get("VOL_RATIO")) else None
    upper_shadow = float(last["UPPER_SHADOW_RATIO"]) if pd.notna(last.get("UPPER_SHADOW_RATIO")) else None
    recent_high_20 = float(df["High"].tail(20).max())
    recent_low_20 = float(df["Low"].tail(20).min())

    timeframe_view = build_multi_timeframe_view(df)
    bullish_evidence: List[str] = []
    bearish_evidence: List[str] = []
    conflicts: List[str] = []

    if timeframe_view["monthly"] in ["上升趋势", "弱修复"]:
        bullish_evidence.append(f"月线视角为{timeframe_view['monthly']}，大方向没有明显失真。")
    elif timeframe_view["monthly"] == "下降趋势":
        bearish_evidence.append("月线仍处下降趋势，所有日线买点都应降权看待。")

    if timeframe_view["weekly"] == "上升趋势":
        bullish_evidence.append("周线保持上升趋势，中期方向对日线信号有支撑。")
    elif timeframe_view["weekly"] == "下降趋势":
        bearish_evidence.append("周线仍偏弱，短期反弹更容易被中期压力打断。")

    if timeframe_view["consistency_score"] >= 3:
        bullish_evidence.append("日线、周线、月线方向基本共振，信号一致性较高。")
    elif timeframe_view["consistency_score"] <= 1:
        conflicts.append("多周期方向并不一致，单看日线容易高估信号质量。")

    if current >= ma20:
        bullish_evidence.append(f"收盘站上 MA20，说明短期结构至少没有继续恶化。")
    else:
        bearish_evidence.append(
            f"收盘低于 MA20，当前收盘 {round_price(current)}，MA20 为 {round_price(ma20)}，说明反弹尚未完成关键修复。"
        )

    if current >= ma60:
        bullish_evidence.append("收盘站上 MA60，中期趋势保持得更完整。")
    else:
        bearish_evidence.append(
            f"收盘低于 MA60，当前收盘 {round_price(current)}，MA60 为 {round_price(ma60)}，中期压力仍然存在。"
        )

    if ret20 is not None:
        if ret20 > 0.05:
            bullish_evidence.append(f"近 20 日收益仍为正，约 {round(ret20 * 100, 2)}%，市场并非持续单边走弱。")
        elif ret20 < -0.08:
            bearish_evidence.append(f"近 20 日收益约 {round(ret20 * 100, 2)}%，最近一个月整体偏弱。")

    if macd_hist is not None:
        if macd_hist > 0:
            bullish_evidence.append("MACD 柱体翻正，动量开始偏向修复。")
        else:
            bearish_evidence.append("MACD 柱体仍未翻正，反弹更像修复而不是转强确认。")

    if adx14 is not None and adx14 < 18:
        conflicts.append(f"ADX14 约为 {round(adx14, 2)}，说明趋势强度本身不高，后续更容易来回拉扯。")
    elif adx14 is not None and adx14 > 25:
        bullish_evidence.append(f"ADX14 约为 {round(adx14, 2)}，当前走势具备一定延续性。")

    if vol_ratio is not None:
        if vol_ratio > 1.5 and current < ma20:
            bearish_evidence.append(
                f"量比约 {round(vol_ratio, 2)}，但价格仍未收复 MA20，放量没有兑现成有效突破，这类形态更偏分歧放大。"
            )
        elif vol_ratio < 0.8 and current >= ma20:
            conflicts.append(f"虽有站稳迹象，但量比仅 {round(vol_ratio, 2)}，突破可信度一般。")

    if upper_shadow is not None and upper_shadow >= 1.2:
        bearish_evidence.append(f"上影比例约 {round(upper_shadow, 2)}，冲高后的承接并不理想。")

    drawdown_20 = (current / recent_high_20 - 1.0) * 100 if recent_high_20 else 0.0
    if drawdown_20 <= -12:
        bearish_evidence.append(f"相对近 20 日高点回撤约 {abs(round(drawdown_20, 2))}%，上方抛压仍需要时间消化。")

    if bullish_evidence and bearish_evidence:
        conflicts.append("多空证据并存时，不能只看单一指标回暖，而要看关键均线和关键价位是否真正被站稳。")

    profile = profile or UserProfile()
    position_view: List[str] = []
    if profile.position_status == "holding" and profile.cost_price is not None:
        pnl_pct = (current / profile.cost_price - 1.0) * 100
        if pnl_pct >= 0:
            position_view.append(f"以成本价 {profile.cost_price} 计算，当前浮盈约 {round(pnl_pct, 2)}%，仓位重点应转向保护利润。")
        else:
            position_view.append(f"以成本价 {profile.cost_price} 计算，当前浮亏约 {abs(round(pnl_pct, 2))}%，仓位重点不该是补仓摊低，而是先确认弱势是否结束。")
        if current < ma20:
            position_view.append("对持仓者而言，价格还没收回 MA20，说明你暂时没有重新拿回主动权。")
        if current > recent_low_20:
            position_view.append("虽然结构偏弱，但尚未跌破近 20 日低点，说明还有观察窗口，不必只按情绪处理。")

    if analysis_mode == "premarket":
        scenario_analysis = [
            f"强修复情景：若今日高开后仍能围绕 {result['trade_plan']['levels']['pullback_buy']} 上方承接，并向 {result['trade_plan']['levels']['breakout_buy']} 进攻，可把它视为修复尝试延续。",
            f"中性震荡情景：若今日在 {result['trade_plan']['levels']['pullback_buy']} 附近反复拉扯，说明资金更偏观望，重点看承接而非预判拉升。",
            f"继续转弱情景：若盘前预案对应的关键防守位 {result['trade_plan']['levels']['stop_price']} 在日内被有效跌破，则应按走弱预案处理。",
        ]
    elif analysis_mode == "intraday":
        scenario_analysis = [
            f"强修复情景：盘中放量突破 {result['trade_plan']['levels']['breakout_buy']} 且回落不破，可视为当日最强信号。",
            f"中性震荡情景：盘中反复测试 {result['trade_plan']['levels']['pullback_buy']} 附近但缺乏持续放量，更像拉锯而不是启动。",
            f"继续转弱情景：盘中跌破 {result['trade_plan']['levels']['stop_price']} 后若反抽无力，通常应优先执行风险控制。 ",
        ]
    else:
        scenario_analysis = [
            f"强修复情景：若后续放量站稳 {result['trade_plan']['levels']['breakout_buy']}，才有资格把当前走势从反弹修复提升为结构转强。",
            f"中性震荡情景：若价格反复围绕 {result['trade_plan']['levels']['pullback_buy']} 附近波动但无法连续站稳，更可能是震荡消化而不是迅速主升。",
            f"继续转弱情景：若收盘跌破 {result['trade_plan']['levels']['stop_price']}，说明这轮修复失败，后续应优先按风险控制处理。",
        ]

    decision_logic = [
        "先看月线、周线、日线是否共振，再判断它是强势延续、弱修复、震荡整理还是中期转弱。",
        "再看量能、MACD、ADX 等是否支持趋势延续，避免把单日反弹误判成反转。",
        "最后把持仓成本、仓位和关键价位叠加，输出真正可执行的仓位建议，而不是停留在指标描述。"
    ]

    return {
        "timeframe_view": timeframe_view,
        "decision_logic": decision_logic,
        "bullish_evidence": bullish_evidence,
        "bearish_evidence": bearish_evidence,
        "conflicts": conflicts,
        "position_view": position_view,
        "scenario_analysis": scenario_analysis,
    }


def render_markdown_report(result: Dict, profile: Optional[UserProfile]) -> str:
    snapshot = result["snapshot"]
    plan = result["trade_plan"]
    reasoning = result["reasoning"]
    interaction = result["interaction"]
    levels = plan["levels"]
    profile_lines = [
        f"- 持仓状态：{profile.position_status if profile else 'unknown'}",
        f"- 成本价：{profile.cost_price if profile and profile.cost_price is not None else '未提供'}",
        f"- 持仓股数：{profile.shares if profile and profile.shares is not None else '未提供'}",
        f"- 风险偏好：{profile.risk_style if profile else 'balanced'}",
        f"- 计划周期：{profile.horizon if profile else 'swing'}",
        f"- 最大可接受亏损：{profile.max_drawdown_pct if profile and profile.max_drawdown_pct is not None else '未提供'}",
    ]
    lines = [
        f"# {result['symbol']} 技术分析报告",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 市场：{result['market']}",
        f"- 最新交易日：{snapshot['date']}",
        "",
        "## 结论摘要",
        "",
        f"- 综合评分：**{result['score']} / 100**",
        f"- 结构分类：**{result['classification']}**",
        f"- 置信度：**{result['confidence']}**",
        f"- 人话结论：{result['narrative_summary']}",
        "",
        "## 价格与结构",
        "",
        f"- 最新收盘：`{levels['current_close']}`",
        f"- MA5 / MA10 / MA20 / MA60：`{levels['ma5']}` / `{levels['ma10']}` / `{levels['ma20']}` / `{levels['ma60']}`",
        f"- 20日高点 / 10日低点 / 20日低点：`{levels['recent_high_20']}` / `{levels['recent_low_10']}` / `{levels['recent_low_20']}`",
        f"- ATR20：`{levels['atr20']}`",
        f"- 多周期判断：月线 `{reasoning['timeframe_view']['monthly']}` / 周线 `{reasoning['timeframe_view']['weekly']}` / 日线 `{reasoning['timeframe_view']['daily']}`",
        f"- 三周期一致性：`{reasoning['timeframe_view']['consistency_score']}` / 3",
        "",
        "## 操作建议",
        "",
        "### 推荐动作",
        "",
    ]
    lines.extend([f"- {item}" for item in plan["actions"]])
    lines.extend([
        "",
        "### 买入条件",
        "",
    ])
    lines.extend([f"- {item}" for item in plan["buy_conditions"]])
    lines.extend([
        "",
        "### 卖出与风控条件",
        "",
    ])
    lines.extend([f"- {item}" for item in plan["sell_conditions"]])
    lines.extend([
        "",
        "### 关键价位",
        "",
        f"- 参考入场区间：`{levels['entry_range_low']}` - `{levels['entry_range_high']}`",
        f"- 突破观察位：`{levels['breakout_buy']}`",
        f"- 回踩观察位：`{levels['pullback_buy']}`",
        f"- 防守止损位：`{levels['stop_price']}`",
        f"- 第一止盈参考：`{levels['take_profit_1']}`",
        f"- 第二止盈参考：`{levels['take_profit_2']}`",
        "",
        "### 仓位与盈亏比",
        "",
        f"- 建议初始仓位：`{plan['position_plan']['initial_position']}`",
        f"- 最大仓位上限：`{plan['position_plan']['max_position']}`",
        f"- 最大亏损空间：`-{plan['risk_reward']['risk_pct']}%`",
        f"- 第一目标盈利空间：`+{plan['risk_reward']['reward_pct_1']}%`，风险收益比约 `1:{plan['risk_reward']['ratio_1']}`",
        f"- 第二目标盈利空间：`+{plan['risk_reward']['reward_pct_2']}%`，风险收益比约 `1:{plan['risk_reward']['ratio_2']}`",
        "",
        "## 互动流程",
        "",
        f"- 分析模式：`{result['analysis_mode']}`",
        f"- 模式提示：{interaction['mode_hint']}",
        "",
        "### 建议先问的问题",
        "",
    ])
    lines.extend([f"- {item}" for item in interaction["first_round_questions"]])
    lines.extend([
        "",
        "### 按需补问",
        "",
    ])
    lines.extend([f"- {item}" for item in interaction["second_round_questions"]])
    lines.extend([
        "",
        "## 推理链",
        "",
        "### 决策步骤",
        "",
    ])
    lines.extend([f"- {item}" for item in reasoning["decision_logic"]])
    lines.extend([
        "",
        "### 偏多证据",
        "",
    ])
    lines.extend([f"- {item}" for item in reasoning["bullish_evidence"]] or ["- 当前没有足够强的偏多证据。"])
    lines.extend([
        "",
        "### 偏空证据",
        "",
    ])
    lines.extend([f"- {item}" for item in reasoning["bearish_evidence"]] or ["- 当前没有足够强的偏空证据。"])
    lines.extend([
        "",
        "### 冲突信号与处理",
        "",
    ])
    lines.extend([f"- {item}" for item in reasoning["conflicts"]] or ["- 当前信号方向相对一致。"])
    lines.extend([
        "",
        "### 持仓视角",
        "",
    ])
    lines.extend([f"- {item}" for item in reasoning["position_view"]] or ["- 当前未提供持仓约束，因此按通用逻辑输出。"])
    lines.extend([
        "",
        "### 情景推演",
        "",
    ])
    lines.extend([f"- {item}" for item in reasoning["scenario_analysis"]])
    lines.extend([
        "",
        "## 信号拆解",
        "",
        "### 正向信号",
        "",
    ])
    lines.extend([f"- {item}" for item in result["positives"]] or ["- 暂无明显强势信号"])
    lines.extend([
        "",
        "### 风险项",
        "",
    ])
    lines.extend([f"- {item}" for item in result["risks"]] or ["- 暂无显著风险项"])
    lines.extend([
        "",
        "### 观察重点",
        "",
    ])
    lines.extend([f"- {item}" for item in result["watch_points"]])
    lines.extend([
        "",
        "## 用户输入",
        "",
    ])
    lines.extend(profile_lines)
    lines.extend([
        "",
        "## 说明",
        "",
        "- 以上价位是基于最新日线结构、均线和波动率生成的操作参考，不是保证成交的指令价。",
        "- 若次日大幅高开、高开低走或出现消息面冲击，应以盘中量价结构重新校正。"
    ])
    return "\n".join(lines) + "\n"


def write_output(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def analyze(
    symbol: str,
    market: str,
    bench_symbol: Optional[str],
    weights: Dict[str, float],
    profile: Optional[UserProfile] = None,
    analysis_mode: str = "close",
) -> Dict:
    df = add_indicators(fetch_data(symbol, market))
    bench_df = None
    if bench_symbol:
        try:
            bench_df = add_indicators(fetch_data(bench_symbol, market if market != "cn" else "cn"))
        except Exception:
            bench_df = None

    last = df.iloc[-1]
    anchor_dt = find_anchor(df)
    anchor = df.loc[anchor_dt] if anchor_dt is not None else None
    post_anchor = df.loc[anchor_dt:] if anchor_dt is not None else None

    results: Dict[str, Optional[float]] = {}
    positives: List[str] = []
    risks: List[str] = []
    watch_points: List[str] = []

    ma_stack = maybe(last.get("MA20"), lambda _: 1.0 if last["MA5"] > last["MA10"] > last["MA20"] else 0.25)
    results["ma_stack"] = ma_stack
    if ma_stack and ma_stack > 0.8:
        positives.append("MA5 > MA10 > MA20，短中期均线多头排列")
    else:
        risks.append("短中期均线未形成强多头排列")

    results["price_above_ma20"] = maybe(last.get("MA20"), lambda _: 1.0 if last["Close"] > last["MA20"] else 0.0)
    results["price_above_ma60"] = maybe(last.get("MA60"), lambda _: 1.0 if last["Close"] > last["MA60"] else 0.0)
    results["ma20_slope"] = maybe(last.get("MA20_SLOPE5"), lambda v: 1.0 if v > 0 else 0.0)
    results["ma60_slope"] = maybe(last.get("MA60_SLOPE5"), lambda v: 1.0 if v > 0 else 0.0)

    results["ret20"] = maybe(last.get("RET20"), lambda v: 1.0 if v > 0.05 else 0.7 if v > 0 else 0.2)
    results["ret60"] = maybe(last.get("RET60"), lambda v: 1.0 if v > 0.12 else 0.7 if v > 0 else 0.2)
    results["drawdown_from_high120"] = maybe(last.get("DD120"), lambda v: 1.0 if v > -0.1 else 0.6 if v > -0.2 else 0.2)

    if anchor is not None and post_anchor is not None and len(post_anchor) >= 2:
        anchor_ret = float(anchor["Close"] / df["Close"].shift(1).loc[anchor_dt] - 1) if anchor_dt in df.index else np.nan
        results["anchor_breakout_strength"] = 1.0 if pd.notna(anchor_ret) and anchor_ret > 0.04 and anchor["VOL_RATIO"] > 1.8 else 0.7

        peak_after_anchor = post_anchor["Close"].max()
        current_close = float(last["Close"])
        pullback_depth = current_close / peak_after_anchor - 1
        results["pullback_depth"] = 1.0 if pullback_depth > -0.05 else 0.65 if pullback_depth > -0.1 else 0.2

        if len(post_anchor) > 1:
            pullback_leg = post_anchor.iloc[1:]
            shrink_ratio = pullback_leg["Volume"].mean() / max(float(anchor["Volume"]), 1.0)
            results["pullback_volume_shrink"] = 1.0 if shrink_ratio < 0.65 else 0.6 if shrink_ratio < 0.9 else 0.2
            results["pullback_days"] = 1.0 if len(pullback_leg) <= 5 else 0.7 if len(pullback_leg) <= 10 else 0.3
            if shrink_ratio < 0.7:
                positives.append("回调阶段量能显著收缩")
            else:
                risks.append("回调阶段缩量不明显")

        dist_risk = 1.0 if (last["UPPER_SHADOW_RATIO"] < 1.2 and last["Close"] >= last["MA20"]) else 0.3
        results["distribution_risk"] = dist_risk
        if dist_risk < 0.5:
            risks.append("存在冲高回落或跌破关键均线的派发风险")
    else:
        results["anchor_breakout_strength"] = None
        results["pullback_depth"] = None
        results["pullback_volume_shrink"] = None
        results["pullback_days"] = None
        results["distribution_risk"] = None
        risks.append("近阶段未识别出明确的放量推升锚点")

    results["rsi14"] = maybe(last.get("RSI14"), lambda v: 1.0 if 50 <= v <= 70 else 0.65 if 40 <= v < 50 or 70 < v <= 80 else 0.3)
    results["macd_hist"] = maybe(last.get("MACD_HIST"), lambda v: 1.0 if v > 0 else 0.2)
    results["adx14"] = maybe(last.get("ADX14"), lambda v: 1.0 if v > 25 else 0.6 if v > 18 else 0.3)
    results["mfi14"] = maybe(last.get("MFI14"), lambda v: 0.9 if 50 <= v <= 80 else 0.5)
    results["stochastic_kd"] = maybe(last.get("K14"), lambda v: 0.8 if 40 <= v <= 85 else 0.4)
    results["cci20"] = maybe(last.get("CCI20"), lambda v: 0.9 if v > 0 else 0.3)
    results["bollinger_pos"] = maybe(last.get("BOLL_POS"), lambda v: 0.9 if 0.5 <= v <= 0.95 else 0.4)
    results["atr20_pct"] = maybe(last.get("ATR20_PCT"), lambda v: 0.8 if v < 0.05 else 0.5 if v < 0.08 else 0.2)
    results["obv_slope"] = maybe(last.get("OBV_SLOPE5"), lambda v: 0.9 if v > 0 else 0.3)
    results["close_in_day_range"] = maybe(last.get("CLOSE_IN_DAY_RANGE"), lambda v: 0.9 if v > 0.65 else 0.4)
    results["upper_shadow_risk"] = maybe(last.get("UPPER_SHADOW_RATIO"), lambda v: 1.0 if v < 1.0 else 0.5 if v < 2.0 else 0.2)

    if bench_df is not None and len(bench_df) >= 30 and len(df) >= 30:
        rs20 = (df["Close"].iloc[-1] / df["Close"].iloc[-21]) / (bench_df["Close"].iloc[-1] / bench_df["Close"].iloc[-21]) - 1
        results["relative_strength_20"] = 1.0 if rs20 > 0.03 else 0.7 if rs20 > 0 else 0.2
        results["bench_trend"] = maybe(bench_df.iloc[-1].get("MA20"), lambda _: 1.0 if bench_df.iloc[-1]["Close"] > bench_df.iloc[-1]["MA20"] else 0.3)
        if rs20 > 0:
            positives.append("20日相对基准强于指数")
        else:
            risks.append("20日相对基准并不占优")
    else:
        results["relative_strength_20"] = None
        results["bench_trend"] = None

    score, used_weight, skipped = score_indicator(results, weights)

    if score >= 70 and results.get("pullback_volume_shrink", 0) and results.get("pullback_depth", 0) and results.get("price_above_ma20", 0):
        classification = "趋势延续型"
        summary = "中期趋势向上，存在放量推升与缩量回调组合，整体更接近健康整理。"
        watch_points.extend(["是否再次放量突破前高", "MA20 是否继续上行", "回调是否继续维持缩量"])
    elif score >= 60 and results.get("anchor_breakout_strength"):
        classification = "试盘整理型"
        summary = "存在阶段性放量推升，但后续是否转强仍需等待再次放量确认。"
        watch_points.extend(["是否重新放量", "是否站稳前高附近", "回调时间是否拖长"])
    elif score >= 45:
        classification = "弱反弹型"
        summary = "短期有修复迹象，但中期趋势与结构优势不足。"
        watch_points.extend(["能否收复 MA20 或 MA60", "MACD 柱体能否翻正", "量能是否回升"])
    elif results.get("distribution_risk") is not None and results.get("distribution_risk", 1) < 0.5:
        classification = "疑似派发型"
        summary = "高位回落或冲高回落风险偏高，更接近派发而非健康整理。"
        watch_points.extend(["是否继续放量下跌", "是否跌破关键均线", "是否出现反抽无量"])
    else:
        classification = "暂无明显优势结构"
        summary = "当前多空信号混杂，缺乏高质量的一致性技术优势。"
        watch_points.extend(["等待更清晰的量价结构", "观察趋势均线方向", "观察关键阻力和支撑"])

    confidence = "高" if used_weight >= 70 else "中" if used_weight >= 45 else "低"

    if results.get("price_above_ma20") == 1.0:
        positives.append("价格站上 MA20")
    if results.get("price_above_ma60") == 1.0:
        positives.append("价格站上 MA60")
    if results.get("macd_hist") == 0.2:
        risks.append("MACD 柱体仍未翻正")
    if results.get("adx14") is not None and results["adx14"] < 0.5:
        risks.append("趋势强度仍然一般")

    snapshot = {
        "date": str(df.index[-1].date()),
        "close": round_price(float(last["Close"])),
        "ma5": round_price(float(last["MA5"])) if pd.notna(last.get("MA5")) else None,
        "ma10": round_price(float(last["MA10"])) if pd.notna(last.get("MA10")) else None,
        "ma20": round_price(float(last["MA20"])) if pd.notna(last.get("MA20")) else None,
        "ma60": round_price(float(last["MA60"])) if pd.notna(last.get("MA60")) else None,
        "atr20": round_price(float(last["ATR20"])) if pd.notna(last.get("ATR20")) else None,
        "volume_ratio": round(float(last["VOL_RATIO"]), 2) if pd.notna(last.get("VOL_RATIO")) else None,
    }
    narrative_summary = (
        f"当前日线结构属于{classification}，最新收盘 {snapshot['close']}。"
        f"{summary} 当前更需要关注 {', '.join(watch_points[:2])}。"
    )
    base_result = {
        "symbol": symbol,
        "market": market,
        "analysis_mode": analysis_mode,
        "score": round(score, 2),
        "confidence": confidence,
        "classification": classification,
        "summary": summary,
        "narrative_summary": narrative_summary,
        "positives": list(dict.fromkeys(positives)),
        "risks": list(dict.fromkeys(risks)),
        "skipped": skipped,
        "watch_points": list(dict.fromkeys(watch_points)),
        "used_weight": round(used_weight, 2),
        "snapshot": snapshot,
    }
    base_result["trade_plan"] = build_trade_plan(base_result, df, bench_df, profile)
    base_result["reasoning"] = build_reasoning(base_result, df, bench_df, profile, analysis_mode)
    base_result["interaction"] = build_interaction_prompts(symbol, profile, analysis_mode)
    return base_result


def load_weights(path: Optional[str]) -> Dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    if not path:
        return weights
    with open(path, "r", encoding="utf-8") as f:
        custom = json.load(f)
    for k, v in custom.items():
        try:
            weights[k] = float(v)
        except Exception:
            pass
    return weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--market", required=True, choices=["cn", "us"])
    parser.add_argument("--bench-symbol", default=None)
    parser.add_argument("--weights-json", default=None)
    parser.add_argument("--analysis-mode", choices=["premarket", "intraday", "close"], default="close")
    parser.add_argument("--position-status", choices=["flat", "holding", "watch", "unknown"], default=None)
    parser.add_argument("--cost-price", type=float, default=None)
    parser.add_argument("--shares", type=int, default=None)
    parser.add_argument("--max-drawdown-pct", type=float, default=None)
    parser.add_argument("--risk-style", choices=["conservative", "balanced", "aggressive"], default="balanced")
    parser.add_argument("--horizon", choices=["short", "swing", "position"], default="swing")
    parser.add_argument("--no-interactive", action="store_true")
    parser.add_argument("--print-question-template", action="store_true")
    parser.add_argument("--markdown-output", default=None)
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    weights = load_weights(args.weights_json)
    profile = collect_user_profile(args)
    if args.print_question_template:
        prompts = build_interaction_prompts(args.symbol, profile, args.analysis_mode)
        print("建议先问的问题:")
        for item in prompts["first_round_questions"]:
            print(f"- {item}")
        print("\n按需补问:")
        for item in prompts["second_round_questions"]:
            print(f"- {item}")
        print(f"\n模式提示: {prompts['mode_hint']}")
        return

    result = analyze(args.symbol, args.market, args.bench_symbol, weights, profile, args.analysis_mode)

    markdown_output = args.markdown_output or f"{args.symbol}_analysis_report.md"
    json_output = args.json_output
    markdown = render_markdown_report(result, profile)
    write_output(markdown_output, markdown)
    if json_output:
        write_output(json_output, json.dumps(result, ensure_ascii=False, indent=2))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        trade_plan = result["trade_plan"]
        levels = trade_plan["levels"]
        print(f"标的: {result['symbol']} ({result['market']})")
        print(f"综合评分: {result['score']} / 100")
        print(f"分类: {result['classification']} | 置信度: {result['confidence']} | 模式: {result['analysis_mode']}")
        print(f"结论: {result['narrative_summary']}")
        print(f"最新收盘: {levels['current_close']} | MA20: {levels['ma20']} | MA60: {levels['ma60']}")
        print(f"突破观察位: {levels['breakout_buy']} | 回踩观察位: {levels['pullback_buy']} | 止损位: {levels['stop_price']}")
        print("\n建议先问的问题:")
        for x in result["interaction"]["first_round_questions"]:
            print(f"- {x}")
        print("\n推荐动作:")
        for x in trade_plan["actions"]:
            print(f"- {x}")
        print("\n买入条件:")
        for x in trade_plan["buy_conditions"]:
            print(f"- {x}")
        print("\n卖出与风控条件:")
        for x in trade_plan["sell_conditions"]:
            print(f"- {x}")
        print("\n信号亮点:")
        for x in result["positives"]:
            print(f"- {x}")
        print("\n主要风险:")
        for x in result["risks"]:
            print(f"- {x}")
        print(f"\nMarkdown 报告已写入: {markdown_output}")
        if json_output:
            print(f"JSON 结果已写入: {json_output}")


if __name__ == "__main__":
    main()
