"""固定几何布局的 Plotly 牛眼图、亮度时间轴及高清 PNG 导出。"""

from numbers import Integral

import numpy as np
import plotly.graph_objects as go

from anatomy import APICAL_VIEW_LABELS, SEGMENTS
from timing import DisplayMode, calculate_brightness, uniform_ts, validate_ts

# Windows/macOS 常见中文字体及 Linux Noto 字体，PNG 使用浏览器的本地字体。
FONT_FAMILY = '"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", Arial, sans-serif'
LOW_COLOR = np.array([218, 225, 233])
HIGH_COLOR = np.array([255, 183, 3])
RING_RADII = {"基底段": (0.69, 1.0), "中段": (0.37, 0.68)}


def _brightness_color(brightness: float) -> str:
    """线性插值浅灰与橙黄；保持颜色与亮度的一一对应。"""
    rgb = np.rint(LOW_COLOR + brightness * (HIGH_COLOR - LOW_COLOR)).astype(int)
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


def _sector_points(center_deg: float, inner: float, outer: float):
    """扇形按数学坐标生成；几何与 Ts、t、σ 无关。"""
    angle = np.deg2rad(np.linspace(center_deg - 30, center_deg + 30, 45))
    x = np.concatenate((outer * np.cos(angle), inner * np.cos(angle[::-1])))
    y = np.concatenate((outer * np.sin(angle), inner * np.sin(angle[::-1])))
    return np.append(x, x[0]), np.append(y, y[0])


def create_bullseye(
    ts_ms,
    t_ms: float,
    sigma_ms: float = 15.0,
    mode: DisplayMode = "flash",
    *,
    show_names: bool = True,
) -> go.Figure:
    """按编号 1–12 绑定 Ts 与标记；本图绝不包含心尖段或心尖帽。"""
    values = validate_ts(ts_ms)
    brightness = calculate_brightness(values, t_ms, sigma_ms, mode)
    fig = go.Figure()
    marker_x, marker_y, hover_data = [], [], []

    for segment, ts, light in zip(SEGMENTS, values, brightness, strict=True):
        inner, outer = RING_RADII[segment.level]
        x, y = _sector_points(segment.center_angle_deg, inner, outer)
        fig.add_trace(
            go.Scatter(
                x=x, y=y, mode="lines", fill="toself",
                fillcolor="#f1f4f8", line={"color": "#c4cdd8", "width": 1.4},
                hoverinfo="skip", showlegend=False,
                name=f"节段 {segment.number} 区域",
            )
        )
        radius = (inner + outer) / 2
        angle = np.deg2rad(segment.center_angle_deg)
        px, py = float(radius * np.cos(angle)), float(radius * np.sin(angle))
        marker_x.append(px)
        marker_y.append(py)
        hover_data.append(
            [segment.number, segment.name, float(ts), float(t_ms), float(light),
             APICAL_VIEW_LABELS[segment.apical_view]]
        )
        if show_names:
            fig.add_annotation(
                x=px, y=py - 0.095, text=segment.name, showarrow=False,
                font={"size": 12, "color": "#334155"},
                xanchor="center", yanchor="middle",
            )

    # 先画柔和光晕，再画固定大小的编号亮点。灰态与峰值的位置完全相同。
    colors = [_brightness_color(float(light)) for light in brightness]
    fig.add_trace(
        go.Scatter(
            x=marker_x, y=marker_y, mode="markers",
            marker={"size": 45, "color": colors, "opacity": 0.24},
            hoverinfo="skip", showlegend=False, name="光晕",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=marker_x, y=marker_y, mode="markers+text",
            text=[str(segment.number) for segment in SEGMENTS],
            textposition="middle center", textfont={"size": 13, "color": "#243047"},
            marker={"size": 30, "color": colors, "line": {"color": "white", "width": 1.5}},
            customdata=hover_data, name="Ts 亮点", showlegend=False,
            hovertemplate=(
                "<b>%{customdata[0]} · %{customdata[1]}</b><br>"
                "Ts = %{customdata[2]:.1f} ms<br>"
                "当前 t = %{customdata[3]:.1f} ms<br>"
                "显示亮度 = %{customdata[4]:.4f}<br>"
                "切面预留：%{customdata[5]}（待医学审核）<extra></extra>"
            ),
        )
    )

    for x, y, label in (
        (0, 1.13, "前壁"), (0, -1.13, "下壁"),
        (-1.12, 0, "间隔"), (1.12, 0, "侧壁"),
    ):
        fig.add_annotation(
            x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
            font={"size": 14, "color": "#475569"},
        )
    fig.add_annotation(
        x=0, y=0, text="心尖部<br>未纳入",
        showarrow=False, font={"size": 16, "color": "#64748b"},
    )
    mode_name = "高斯闪烁" if mode == "flash" else "到达后保持"
    peak_label = (
        f"统一 Ts = {values[0]:g} ms" if np.all(values == values[0])
        else f"Ts 范围 = {np.min(values):g}–{np.max(values):g} ms"
    )
    fig.update_layout(
        title={
            "text": "<b>左心室12节段 Ts 示意图</b><br>"
                    "<sup>外环：基底段 1–6 ｜ 内环：中段 7–12 ｜ 不含心尖部</sup>",
            "x": 0.5, "xanchor": "center", "y": 0.98,
            "font": {"size": 19, "color": "#172b4d"},
        },
        height=680, width=680, margin={"l": 20, "r": 20, "t": 76, "b": 90},
        paper_bgcolor="white", plot_bgcolor="white", font={"family": FONT_FAMILY},
        xaxis={"range": [-1.27, 1.27], "visible": False, "fixedrange": True,
               "constrain": "domain"},
        yaxis={"range": [-1.27, 1.27], "visible": False, "fixedrange": True,
               "scaleanchor": "x", "scaleratio": 1, "constrain": "domain"},
        hoverlabel={"bgcolor": "white", "font_size": 14},
        dragmode=False,
        annotations=list(fig.layout.annotations) + [
            {"x": 0.5, "y": -0.04, "xref": "paper", "yref": "paper", "showarrow": False,
             "text": f"t = {t_ms:g} ms ｜ {peak_label} ｜ σ = {sigma_ms:g} ms ｜ {mode_name}",
             "font": {"size": 12, "color": "#64748b"}},
            {"x": 0.5, "y": -0.075, "xref": "paper", "yref": "paper", "showarrow": False,
             "text": "演示模型 · 方位及切面映射待医学审核 · 不提供正常参考值",
             "font": {"size": 10, "color": "#64748b"}},
        ],
    )
    return fig


def create_timeline(
    ts_ms: float, t_ms: float, sigma_ms: float = 15.0, mode: DisplayMode = "flash",
) -> go.Figure:
    """理想同步模式：12 条亮度曲线重合，以一条曲线表示。"""
    values = uniform_ts(ts_ms)
    # 调用纯计算接口验证参数；包括合法但无效的显示模式。
    current_light = float(calculate_brightness(values, t_ms, sigma_ms, mode)[0])
    times = np.arange(0, 601, dtype=float)
    lights = np.array([calculate_brightness(values, time, sigma_ms, mode)[0] for time in times])
    fig = go.Figure(
        go.Scatter(
            x=times, y=lights, mode="lines", line={"color": "#f59e0b", "width": 3},
            fill="tozeroy", fillcolor="rgba(245,158,11,0.12)",
            name="12节段共用亮度", hovertemplate="t = %{x:.0f} ms<br>L = %{y:.4f}<extra></extra>",
        )
    )
    fig.add_vline(x=float(ts_ms), line_dash="dash", line_color="#94a3b8",
                  annotation_text="统一 Ts", annotation_position="top right")
    fig.add_vline(x=float(t_ms), line_color="#2563eb", line_width=2)
    fig.add_trace(go.Scatter(x=[float(t_ms)], y=[current_light], mode="markers",
                             marker={"size": 11, "color": "#2563eb"}, name="当前时间"))
    fig.update_layout(
        height=210, margin={"l": 35, "r": 25, "t": 22, "b": 40}, showlegend=False,
        font={"family": FONT_FAMILY}, paper_bgcolor="white", plot_bgcolor="white",
        xaxis={"title": "时间 t (ms)", "range": [0, 600], "fixedrange": True,
               "gridcolor": "#edf1f5", "tick0": 0, "dtick": 100},
        yaxis={"title": "显示亮度 L", "range": [-0.02, 1.12], "fixedrange": True,
               "gridcolor": "#edf1f5", "tickvals": [0, 0.5, 1]},
        dragmode=False,
    )
    return fig


class ImageExportError(RuntimeError):
    """可在界面友好显示的导出失败，不影响计算、CSV 或牛眼图。"""


def export_png(fig: go.Figure, *, width: int = 1000, height: int = 1000, scale: int = 2) -> bytes:
    """默认输出 2000×2000 PNG。Kaleido 1.x 需要系统 Chrome/Chromium。"""
    for value, label in ((width, "宽度"), (height, "高度"), (scale, "倍率")):
        if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
            raise ValueError(f"PNG {label}必须为正整数。")
    try:
        return fig.to_image(format="png", width=int(width), height=int(height), scale=int(scale))
    except Exception as exc:
        raise ImageExportError(
            "PNG 导出失败。请安装 requirements.txt 中配套的 Plotly/Kaleido，"
            "并确认本机已安装 Google Chrome 或 Chromium。"
            "若浏览器安装在非默认位置，可设置 BROWSER_PATH 为浏览器可执行文件路径。"
            f"\n底层信息：{type(exc).__name__}: {exc}"
        ) from exc
