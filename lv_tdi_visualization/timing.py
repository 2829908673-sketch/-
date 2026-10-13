"""Ts 与显示亮度的纯计算模块，可在未来接收 12 个不同的 Ts。

单位均为毫秒。亮度是显示算法，既不是组织速度曲线，也不是收缩力。
"""

from dataclasses import dataclass
from numbers import Real
from typing import Iterable, Literal

import numpy as np
import pandas as pd

SEGMENT_COUNT = 12
DisplayMode = Literal["flash", "hold"]


def _time_parameter(value: Real, name: str, *, positive: bool = False) -> float:
    """只接受有限实数；bool 在 Python 中也是整数，须明确排除。"""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name}必须为有限实数，单位为 ms。")
    result = float(value)
    if not np.isfinite(result) or result < 0 or (positive and result == 0):
        condition = "大于 0" if positive else "大于或等于 0"
        raise ValueError(f"{name}必须为有限实数且{condition} ms。")
    return result


def validate_ts(ts_ms: Iterable[float]) -> np.ndarray:
    """按编号 1–12 检查一维 Ts 数组；返回副本，防止调用者意外修改。"""
    try:
        # 保留原始类型，防止 [True, 300, ...] 被 NumPy 自动合并为整数。
        source = ts_ms if isinstance(ts_ms, np.ndarray) else list(ts_ms)
        original = np.asarray(source, dtype=object)
        raw = np.asarray(source)
    except (TypeError, ValueError) as exc:
        raise ValueError("Ts 必须是按节段编号排列的 12 个有限非负实数。") from exc
    if raw.shape != (SEGMENT_COUNT,):
        raise ValueError("Ts 必须是一维数组，且恰好包含 12 个节段。")
    if raw.dtype.kind not in "iuf" or any(isinstance(item, (bool, np.bool_)) for item in original.flat):
        raise ValueError("Ts 必须为实数，不能包含文字、布尔值或复数。")
    values = raw.astype(float, copy=True)
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("每个节段的 Ts 必须是有限且大于或等于 0 的实数。")
    return values


def uniform_ts(ts_ms: float = 300.0) -> np.ndarray:
    """生成理想同步模式的数据，不绑定界面的 100–500 ms 范围。"""
    return np.full(SEGMENT_COUNT, _time_parameter(ts_ms, "统一 Ts"), dtype=float)


@dataclass(frozen=True)
class TimingMetrics:
    mean_ts_ms: float
    ts_sd12_ms: float
    max_delay_ms: float
    earliest_ts_ms: float
    latest_ts_ms: float


def compute_metrics(ts_ms: Iterable[float]) -> TimingMetrics:
    """计算时序指标。Ts-SD12 在本软件中明确使用样本标准差（ddof=1）。

    该约定须在未来患者研究方案中复核；本版本不提供正常值或诊断阈值。
    """
    values = validate_ts(ts_ms)
    earliest, latest = float(np.min(values)), float(np.max(values))
    # 浮点数的求和舍入可能让完全相同的非整数 Ts 得到极小的伪标准差。
    synchronous = bool(np.all(values == values[0]))
    return TimingMetrics(
        mean_ts_ms=float(values[0]) if synchronous else float(np.mean(values)),
        ts_sd12_ms=0.0 if synchronous else float(np.std(values, ddof=1)),
        max_delay_ms=latest - earliest,
        earliest_ts_ms=earliest,
        latest_ts_ms=latest,
    )


def calculate_brightness(
    ts_ms: Iterable[float],
    t_ms: float,
    sigma_ms: float = 15.0,
    mode: DisplayMode = "flash",
) -> np.ndarray:
    """高斯闪烁，或峰值前使用高斯、到达后保持 1 的显示模式。

    flash: L_i(t) = exp[-(t - Ts_i)^2 / (2 sigma^2)]。
    hold: t >= Ts_i 时为 1，其余时间仍使用同一高斯函数。
    两种模式的亮起都只表示到达预设 Ts，不表示电激动或收缩开始。
    """
    values = validate_ts(ts_ms)
    current = _time_parameter(t_ms, "当前时间 t")
    width = _time_parameter(sigma_ms, "亮点宽度 σ", positive=True)
    if mode not in ("flash", "hold"):
        raise ValueError("显示模式必须是 'flash'（瞬时闪烁）或 'hold'（到达后保持）。")
    # 极大但有限的时间差可使平方溢出，此时高斯亮度数学上趋近 0。
    with np.errstate(over="ignore", under="ignore"):
        brightness = np.exp(-0.5 * np.square((current - values) / width))
    if mode == "hold":
        brightness = np.where(current >= values, 1.0, brightness)
    return brightness


def build_segment_table(
    ts_ms: Iterable[float],
    t_ms: float,
    sigma_ms: float = 15.0,
    mode: DisplayMode = "flash",
) -> pd.DataFrame:
    """生成按编号排列的表格；同一份数据用于界面及 CSV 导出。"""
    # 局部导入让核心数学模块可以独立使用，同时避免重复维护名称表。
    from anatomy import SEGMENTS

    values = validate_ts(ts_ms)
    current = _time_parameter(t_ms, "当前时间 t")
    brightness = calculate_brightness(values, current, sigma_ms, mode)
    return pd.DataFrame(
        {
            "节段编号": [segment.number for segment in SEGMENTS],
            "中文名称": [segment.name for segment in SEGMENTS],
            "Ts (ms)": values,
            "当前时间 t (ms)": np.full(SEGMENT_COUNT, current),
            "σ (ms)": np.full(SEGMENT_COUNT, float(sigma_ms)),
            "显示模式": ["瞬时闪烁" if mode == "flash" else "到达后保持高亮"] * SEGMENT_COUNT,
            "当前亮度": brightness,
            "是否已经达到峰值": current >= values,
        }
    )


def export_csv(
    ts_ms: Iterable[float],
    t_ms: float,
    sigma_ms: float = 15.0,
    mode: DisplayMode = "flash",
) -> bytes:
    """UTF-8 BOM 让 Windows Excel 直接打开时能正确识别中文。"""
    table = build_segment_table(ts_ms, t_ms, sigma_ms, mode)
    return table.to_csv(index=False, float_format="%.8g").encode("utf-8-sig")
