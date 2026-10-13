"""验证同步模型、未来不同 Ts 的接口、非法输入和 CSV 数据一致性。"""

from io import BytesIO
from math import exp, sqrt

import numpy as np
import pandas as pd
import pytest

from timing import (
    build_segment_table,
    calculate_brightness,
    compute_metrics,
    export_csv,
    uniform_ts,
    validate_ts,
)


def test_default_synchrony_has_zero_dispersion():
    """验收：12 个 Ts 默认均为 300 ms，离散程度必须严格为零。"""
    values = uniform_ts()
    np.testing.assert_array_equal(values, np.full(12, 300.0))
    metrics = compute_metrics(values)
    assert metrics.mean_ts_ms == 300.0
    assert metrics.ts_sd12_ms == 0.0
    assert metrics.max_delay_ms == 0.0
    assert metrics.earliest_ts_ms == 300.0
    assert metrics.latest_ts_ms == 300.0


@pytest.mark.parametrize("peak", [100.0, 300.0, 300.1, 425.0, 500.0])
def test_all_segments_peak_at_the_configured_uniform_ts(peak):
    """验收：改变统一 Ts 后，全部节段仍在新的时间同时达到最大亮度。"""
    values = uniform_ts(peak)
    np.testing.assert_array_equal(calculate_brightness(values, peak), np.ones(12))
    assert compute_metrics(values).mean_ts_ms == peak
    assert compute_metrics(values).ts_sd12_ms == 0.0
    assert compute_metrics(values).max_delay_ms == 0.0


def test_changing_peak_moves_all_twelve_peaks_together():
    before = uniform_ts(300)
    after = uniform_ts(425)
    np.testing.assert_array_equal(after - before, np.full(12, 125))
    assert np.all(calculate_brightness(after, 300) < 1e-10)
    np.testing.assert_array_equal(calculate_brightness(after, 425), np.ones(12))


@pytest.mark.parametrize("current", [0, 600])
def test_gaussian_brightness_is_negligible_far_from_peak(current):
    """距离峰值 20 个 σ 时，亮度应接近零但不能出现负数或 NaN。"""
    brightness = calculate_brightness(uniform_ts(), current)
    assert np.all(np.isfinite(brightness))
    assert np.all(brightness >= 0)
    assert np.all(brightness < 1e-50)


def test_gaussian_width_and_symmetry_have_expected_meaning():
    # 由高斯定义手算：离峰值一个 σ 的亮度应为 exp(-1/2)。
    left = calculate_brightness(uniform_ts(), 285, sigma_ms=15)
    right = calculate_brightness(uniform_ts(), 315, sigma_ms=15)
    np.testing.assert_allclose(left, np.full(12, exp(-0.5)), rtol=1e-14)
    np.testing.assert_array_equal(left, right)
    assert np.all(calculate_brightness(uniform_ts(), 285, sigma_ms=30) > left)


def test_nonuniform_ts_metrics_use_sample_standard_deviation():
    """V1.0 接口：前六段 100、后六段 200，均值 150。

    十二个偏差平方之和为 12×50²=30000，样本方差为 30000/11。
    这一独立手算例子可发现错误使用总体标准差或错误节段数量。
    """
    metrics = compute_metrics([100] * 6 + [200] * 6)
    assert metrics.mean_ts_ms == 150
    assert metrics.ts_sd12_ms == pytest.approx(sqrt(30000 / 11))
    assert metrics.max_delay_ms == 100
    assert metrics.earliest_ts_ms == 100
    assert metrics.latest_ts_ms == 200


def test_different_segments_use_their_own_peak_times():
    values = np.arange(100, 220, 10, dtype=float)
    for index, peak in enumerate(values):
        brightness = calculate_brightness(values, float(peak), sigma_ms=5)
        assert brightness[index] == 1
        assert int(np.argmax(brightness)) == index
        assert np.count_nonzero(brightness == 1) == 1
        assert np.all((brightness >= 0) & (brightness <= 1))


def test_hold_mode_before_at_and_after_each_peak():
    # 在 t=300 时，280 已过去、300 正好达到、320 尚未达到峰值。
    values = [280, 300, 320] * 4
    brightness = calculate_brightness(values, 300, sigma_ms=20, mode="hold")
    np.testing.assert_allclose(brightness, [1, 1, exp(-0.5)] * 4)
    np.testing.assert_array_equal(
        calculate_brightness(values, 600, mode="hold"), np.ones(12)
    )
    assert np.all(calculate_brightness(values, 600, mode="flash") < 1e-50)


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), True, "300", None])
def test_invalid_uniform_ts_raises_a_clear_error(bad):
    with pytest.raises(ValueError, match="统一 Ts"):
        uniform_ts(bad)


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), True, "300", None])
def test_invalid_current_time_raises_a_clear_error(bad):
    with pytest.raises(ValueError, match="当前时间 t"):
        calculate_brightness(uniform_ts(), bad)


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), True, "15", None])
def test_invalid_sigma_raises_a_clear_error(bad):
    with pytest.raises(ValueError, match="亮点宽度 σ"):
        calculate_brightness(uniform_ts(), 300, sigma_ms=bad)


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [300] * 11,
        [300] * 13,
        [[300] * 6] * 2,
        [-1] + [300] * 11,
        [float("nan")] + [300] * 11,
        [float("inf")] + [300] * 11,
        [True] * 12,
        [True] + [300] * 11,
        ["300"] * 12,
        [300 + 0j] * 12,
    ],
)
def test_invalid_segment_times_raise_value_error(bad):
    with pytest.raises(ValueError, match="Ts"):
        validate_ts(bad)


def test_unknown_display_mode_raises_clear_error():
    with pytest.raises(ValueError, match="显示模式"):
        calculate_brightness(uniform_ts(), 300, mode="unknown")


def test_timing_functions_do_not_modify_input():
    original = np.arange(100, 220, 10, dtype=float)
    snapshot = original.copy()
    validated = validate_ts(original)
    validated[0] = 999
    compute_metrics(original)
    calculate_brightness(original, 150)
    build_segment_table(original, 150)
    export_csv(original, 150)
    np.testing.assert_array_equal(original, snapshot)


def test_ts_iterable_accepts_a_generator():
    """后续读取数据时，按编号生成的一次性 iterable 也可输入接口。"""
    np.testing.assert_array_equal(
        validate_ts(100 + 10 * index for index in range(12)),
        np.arange(100, 220, 10, dtype=float),
    )


def test_table_flags_reached_peak_independently_of_flash_brightness():
    values = [280, 300, 320] * 4
    table = build_segment_table(values, 300, sigma_ms=20)
    assert table["是否已经达到峰值"].tolist() == [True, True, False] * 4
    np.testing.assert_allclose(table["当前亮度"], [exp(-0.5), 1, exp(-0.5)] * 4)


def test_exported_csv_preserves_all_twelve_segments_and_chinese_names():
    """验收：CSV 含 12 个节段，BOM 便于 Windows Excel 识别中文。"""
    values = np.arange(100, 220, 10, dtype=float)
    content = export_csv(values, 150, sigma_ms=15, mode="hold")
    assert content.startswith(b"\xef\xbb\xbf")
    table = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
    assert len(table) == 12
    assert table["节段编号"].tolist() == list(range(1, 13))
    assert table.loc[0, "中文名称"] == "基底前壁"
    assert table.loc[6, "中文名称"] == "中段前壁"
    assert table["中文名称"].nunique() == 12
    np.testing.assert_array_equal(table["Ts (ms)"], values)
    np.testing.assert_array_equal(table["当前时间 t (ms)"], np.full(12, 150))
    np.testing.assert_array_equal(table["σ (ms)"], np.full(12, 15))
    assert table["显示模式"].tolist() == ["到达后保持高亮"] * 12
    assert table["是否已经达到峰值"].tolist() == [True] * 6 + [False] * 6
    np.testing.assert_allclose(
        table["当前亮度"],
        calculate_brightness(values, 150, sigma_ms=15, mode="hold"),
        rtol=1e-7,
        atol=1e-10,
    )
