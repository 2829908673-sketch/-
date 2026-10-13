"""使用 Streamlit 内建 AppTest 验证真实界面流程，无需浏览器或自动刷新。

PNG 图像本身另由导出集成检查验证；这里替换导出函数，专门检查界面
收到导出结果或失败后是否正确反馈，避免测试依赖本机 Chrome 安装状态。
"""

import json
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

import visualization


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def app():
    """每个用例使用独立 session_state，避免滑块状态相互影响。"""
    result = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    assert not result.exception
    return result


def _metric(app, label):
    return next(element.value for element in app.metric if element.label == label)


def _button(app, label):
    return next(element for element in app.button if element.label == label)


def _peak_marker(app):
    """读取界面实际送出的 Plotly 数据，检查亮点和表格的一致性。"""
    figure = json.loads(app.get("plotly_chart")[0].proto.spec)
    return next(trace for trace in figure["data"] if trace["name"] == "Ts 亮点")


def test_default_page_renders_twelve_grey_segments_and_zero_reached(app):
    assert len(app.get("plotly_chart")) == 2
    assert app.slider(key="ts_ms").value == 300
    assert app.slider(key="t_ms").value == 0
    assert app.slider(key="sigma_ms").value == 15
    assert app.radio(key="mode_label").value == "瞬时闪烁"
    assert _metric(app, "当前时间 t") == "0 ms"
    assert _metric(app, "统一峰值时间 Ts") == "300 ms"
    assert _metric(app, "Ts-SD12") == "0.0 ms"
    assert _metric(app, "最大节段时间差") == "0.0 ms"
    assert _metric(app, "已达到峰值时间的节段") == "0 / 12"

    table = app.dataframe[0].value
    assert table["节段编号"].tolist() == list(range(1, 13))
    np.testing.assert_array_equal(table["Ts (ms)"], np.full(12, 300))
    assert np.all(table["当前亮度"] < 1e-50)
    assert not table["是否已经达到峰值"].any()
    marker = _peak_marker(app)
    assert marker["text"] == [str(number) for number in range(1, 13)]
    assert marker["marker"]["color"] == ["rgb(218, 225, 233)"] * 12


def test_time_slider_makes_all_twelve_markers_reach_peak(app):
    app.slider(key="t_ms").set_value(300).run()
    assert not app.exception
    assert _metric(app, "当前时间 t") == "300 ms"
    assert _metric(app, "已达到峰值时间的节段") == "12 / 12"
    table = app.dataframe[0].value
    np.testing.assert_array_equal(table["当前亮度"], np.ones(12))
    assert table["是否已经达到峰值"].all()
    marker = _peak_marker(app)
    assert marker["marker"]["color"] == ["rgb(255, 183, 3)"] * 12
    assert [row[4] for row in marker["customdata"]] == [1.0] * 12


def test_browser_camera_exports_current_state_at_ppt_resolution(app):
    """主图内建相机固定输出 2000×2000，文件名跟随当前参数。"""
    app.slider(key="ts_ms").set_value(425).run()
    app.slider(key="t_ms").set_value(425).run()
    config = json.loads(app.get("plotly_chart")[0].proto.config)
    assert config["displayModeBar"] is True
    assert config["modeBarButtons"] == [["toImage"]]
    options = config["toImageButtonOptions"]
    assert options["format"] == "png"
    assert options["filename"] == "lv12_Ts425_t425_flash"
    assert options["width"] * options["scale"] == 2000
    assert options["height"] * options["scale"] == 2000
    assert not app.exception


def test_changing_uniform_ts_updates_table_metrics_and_all_marker_times(app):
    app.slider(key="t_ms").set_value(300).run()
    app.slider(key="ts_ms").set_value(425).run()
    assert not app.exception
    assert _metric(app, "统一峰值时间 Ts") == "425 ms"
    assert _metric(app, "已达到峰值时间的节段") == "0 / 12"
    table = app.dataframe[0].value
    np.testing.assert_array_equal(table["Ts (ms)"], np.full(12, 425))
    assert np.all(table["当前亮度"] < 1e-10)
    assert [row[2] for row in _peak_marker(app)["customdata"]] == [425.0] * 12

    app.slider(key="t_ms").set_value(425).run()
    assert not app.exception
    np.testing.assert_array_equal(app.dataframe[0].value["当前亮度"], np.ones(12))
    assert _metric(app, "已达到峰值时间的节段") == "12 / 12"
    assert _metric(app, "Ts-SD12") == "0.0 ms"
    assert _metric(app, "最大节段时间差") == "0.0 ms"


def test_hold_mode_stays_bright_after_peak_and_flash_mode_fades(app):
    app.radio(key="mode_label").set_value("到达后保持高亮").run()
    app.slider(key="t_ms").set_value(600).run()
    assert not app.exception
    np.testing.assert_array_equal(app.dataframe[0].value["当前亮度"], np.ones(12))
    assert _metric(app, "已达到峰值时间的节段") == "12 / 12"

    app.radio(key="mode_label").set_value("瞬时闪烁").run()
    assert not app.exception
    assert np.all(app.dataframe[0].value["当前亮度"] < 1e-50)
    # 到达标记独立于当前亮度；闪烁过去后计数不会归零。
    assert _metric(app, "已达到峰值时间的节段") == "12 / 12"


def test_jump_to_peak_and_reset_callbacks_work_after_changing_parameters(app):
    app.slider(key="ts_ms").set_value(450).run()
    app.slider(key="sigma_ms").set_value(35).run()
    app.radio(key="mode_label").set_value("到达后保持高亮").run()
    app.checkbox(key="show_names").set_value(False).run()
    _button(app, "跳到统一 Ts（同时最亮）").click().run()
    assert not app.exception
    assert app.slider(key="t_ms").value == 450
    np.testing.assert_array_equal(app.dataframe[0].value["当前亮度"], np.ones(12))

    _button(app, "重置参数").click().run()
    assert not app.exception
    assert app.slider(key="ts_ms").value == 300
    assert app.slider(key="t_ms").value == 0
    assert app.slider(key="sigma_ms").value == 15
    assert app.radio(key="mode_label").value == "瞬时闪烁"
    assert app.checkbox(key="show_names").value is True
    assert _metric(app, "已达到峰值时间的节段") == "0 / 12"


def test_step_buttons_keep_time_within_slider_bounds(app):
    _button(app, "后退 5 ms").click().run()
    assert app.slider(key="t_ms").value == 0
    _button(app, "前进 5 ms").click().run()
    assert app.slider(key="t_ms").value == 5
    app.slider(key="t_ms").set_value(598).run()
    _button(app, "前进 5 ms").click().run()
    assert app.slider(key="t_ms").value == 600
    _button(app, "后退 5 ms").click().run()
    assert app.slider(key="t_ms").value == 595
    assert not app.exception


def test_png_export_failure_shows_help_and_keeps_chart_and_csv_available(app, monkeypatch):
    def fail_export(_figure):
        raise visualization.ImageExportError("测试模拟：浏览器未安装。")

    # app.py 每次 rerun 会重新 from visualization import，因此在按钮运行前替换即可。
    monkeypatch.setattr(visualization, "export_png", fail_export)
    _button(app, "生成当前图的高清 PNG").click().run()
    assert not app.exception
    assert any("相机按钮下载 PNG" in error.value for error in app.error)
    assert any("Chrome/Chromium" in warning.value for warning in app.warning)
    assert any("测试模拟：浏览器未安装" in text.value for text in app.text)
    assert len(app.get("plotly_chart")) == 2
    assert len(app.dataframe[0].value) == 12
    assert "png_export" not in app.session_state
    assert [element.proto.label for element in app.get("download_button")] == ["下载12节段 CSV"]


def test_png_cache_is_invalidated_when_visualization_parameters_change(app, monkeypatch):
    calls = []

    def successful_export(figure):
        calls.append(figure)
        return b"test png bytes"

    monkeypatch.setattr(visualization, "export_png", successful_export)
    _button(app, "生成当前图的高清 PNG").click().run()
    assert not app.exception
    assert len(calls) == 1
    assert app.session_state["png_export"][1] == b"test png bytes"
    assert "下载当前高清 PNG" in [element.proto.label for element in app.get("download_button")]

    app.slider(key="t_ms").set_value(300).run()
    assert not app.exception
    assert "png_export" not in app.session_state
    assert len(calls) == 1
    assert "下载当前高清 PNG" not in [element.proto.label for element in app.get("download_button")]
