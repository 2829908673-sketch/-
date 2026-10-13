"""检查图形与节段数据的真实绑定、固定布局及导出失败提示。"""

import numpy as np
import pytest
import plotly.graph_objects as go

from anatomy import SEGMENTS
from timing import uniform_ts
from visualization import ImageExportError, create_bullseye, create_timeline, export_png


def test_markers_preserve_segment_number_name_and_individual_ts():
    values = np.arange(100, 220, 10)
    figure = create_bullseye(values, 150, sigma_ms=5)
    markers = figure.data[-1]
    assert markers.text == tuple(str(number) for number in range(1, 13))
    assert [row[0] for row in markers.customdata] == list(range(1, 13))
    assert [row[1] for row in markers.customdata] == [segment.name for segment in SEGMENTS]
    assert [row[2] for row in markers.customdata] == list(values)
    assert markers.customdata[5][4] == 1  # 第六段 Ts=150，当前只有它达到峰值。
    assert sum(row[4] == 1 for row in markers.customdata) == 1


def test_time_parameters_change_colors_without_moving_the_geometry():
    before = create_bullseye(uniform_ts(300), 0)
    peak = create_bullseye(uniform_ts(420), 420, sigma_ms=40, mode="hold")
    assert len(before.data) == len(peak.data) == 14  # 12区域、光晕和亮点。
    for before_trace, after_trace in zip(before.data, peak.data, strict=True):
        np.testing.assert_array_equal(before_trace.x, after_trace.x)
        np.testing.assert_array_equal(before_trace.y, after_trace.y)
    assert before.data[-1].marker.color != peak.data[-1].marker.color
    assert len(set(peak.data[-1].marker.color)) == 1
    assert all(row[4] == 1 for row in peak.data[-1].customdata)


def test_anterior_inferior_and_ring_positions_are_explicit():
    points = create_bullseye(uniform_ts(), 300).data[-1]
    assert points.y[0] > 0 and points.y[3] < 0  # 前上、下下。
    assert points.x[1] < 0 and points.x[4] > 0  # 间隔左、侧壁右。
    for index in range(6):
        assert np.hypot(points.x[index], points.y[index]) > np.hypot(
            points.x[index + 6], points.y[index + 6]
        )
    # 这些测试证明软件显示约定，不证明真实解剖/切面的医学正确性。


def test_timeline_has_exact_peak_and_current_time_in_both_modes():
    flash = create_timeline(300, 300)
    assert flash.data[0].y[300] == 1
    assert flash.data[-1].y[0] == 1
    hold = create_timeline(350, 600, mode="hold")
    assert hold.data[0].y[349] < 1
    assert hold.data[0].y[350] == hold.data[0].y[600] == 1


def test_png_failure_explains_browser_requirement(monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("test browser not found")

    monkeypatch.setattr(go.Figure, "to_image", unavailable)
    with pytest.raises(ImageExportError, match="Chrome"):
        export_png(create_bullseye(uniform_ts(), 300))


@pytest.mark.parametrize("kwargs", [{"width": 0}, {"height": -1}, {"scale": True}])
def test_png_dimensions_require_positive_integers(kwargs):
    with pytest.raises(ValueError, match="正整数"):
        export_png(create_bullseye(uniform_ts(), 300), **kwargs)
