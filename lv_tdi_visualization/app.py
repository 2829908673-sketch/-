"""Streamlit 中文主程序：在本文件目录执行 python -m streamlit run app.py。"""

import numpy as np
import streamlit as st

from anatomy import ANATOMY_REVIEW_STATUS, APICAL_VIEW_LABELS, APICAL_VIEW_SEGMENTS
from timing import build_segment_table, compute_metrics, export_csv, uniform_ts
from visualization import ImageExportError, create_bullseye, create_timeline, export_png

DEFAULTS = {"ts_ms": 300, "t_ms": 0, "sigma_ms": 15, "mode_label": "瞬时闪烁", "show_names": True}
DISPLAY_MODES = {"瞬时闪烁": "flash", "到达后保持高亮": "hold"}


def reset_parameters():
    """回调在下一次渲染控件前运行，避免修改已实例化控件的状态。"""
    st.session_state.update(DEFAULTS)
    st.session_state.pop("png_export", None)


def set_time_to_peak():
    st.session_state.t_ms = st.session_state.ts_ms


def step_time(delta: int):
    st.session_state.t_ms = max(0, min(600, st.session_state.t_ms + delta))


def main():
    st.set_page_config(page_title="左心室12节段时序 V0.1", page_icon="🫀", layout="wide")
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)

    st.title("左心室12节段收缩峰值时序可视化系统 V0.1")
    st.subheader("基于组织多普勒峰值时间的简化数字化模型")
    st.info(
        "亮起仅表示该节段到达预设的组织多普勒收缩期速度峰值时间 Ts。"
        "不表示电激动、真实收缩开始、收缩幅度或收缩力。默认 Ts=300 ms 仅为演示参数。"
    )

    with st.sidebar:
        st.header("参数设置")
        st.caption("理想同步模式 · 12 个节段使用同一个 Ts")
        ts = st.slider("统一峰值时间 Ts (ms)", 100, 500, step=1, key="ts_ms")
        current = st.slider("当前时间 t (ms)", 0, 600, step=1, key="t_ms")
        sigma = st.slider("亮点持续宽度 σ (ms)", 5, 50, step=1, key="sigma_ms",
                          help="高斯宽度参数，并非亮起的绝对起止时刻；σ 越大，显示变化越缓慢。")
        mode_label = st.radio("亮点显示方式", list(DISPLAY_MODES), key="mode_label")
        show_names = st.checkbox("显示中文节段名称", key="show_names")
        st.button("重置参数", on_click=reset_parameters, width="stretch")
        st.caption("手动拖动时间轴即可演示，无需自动刷新或动画插件。")

    mode = DISPLAY_MODES[mode_label]
    values = uniform_ts(ts)
    metrics = compute_metrics(values)
    table = build_segment_table(values, current, sigma, mode)
    reached = int(np.count_nonzero(table["是否已经达到峰值"].to_numpy()))
    fig = create_bullseye(values, current, sigma, mode, show_names=show_names)

    chart_column, results_column = st.columns([1.65, 1], gap="large")
    with chart_column:
        st.plotly_chart(fig, use_container_width=True, key="bullseye", config={
            # 浏览器直接导出不依赖本机 Kaleido/Chrome，Windows/macOS 同样可用。
            "displayModeBar": True, "displaylogo": False, "scrollZoom": False,
            "modeBarButtons": [["toImage"]],
            "toImageButtonOptions": {
                "format": "png", "filename": f"lv12_Ts{ts}_t{current}_{mode}",
                "width": 1000, "height": 1000, "scale": 2,
            },
        })
        st.caption("上：前壁 · 下：下壁 · 左：间隔 · 右：侧壁。方位及切面映射待医学审核。")
        st.caption("高清 PNG：点击牛眼图右上角的相机按钮，直接下载当前图（2000×2000）。")

    with results_column:
        st.markdown("### 实时时序结果")
        a, b = st.columns(2)
        a.metric("当前时间 t", f"{current} ms")
        b.metric("统一峰值时间 Ts", f"{ts} ms")
        a.metric("Ts-SD12", f"{metrics.ts_sd12_ms:.1f} ms")
        b.metric("最大节段时间差", f"{metrics.max_delay_ms:.1f} ms")
        st.metric("已达到峰值时间的节段", f"{reached} / 12")
        st.caption(
            f"Ts 平均值：{metrics.mean_ts_ms:.1f} ms\n\n"
            f"最早峰值：{metrics.earliest_ts_ms:.1f} ms · 最晚峰值：{metrics.latest_ts_ms:.1f} ms"
        )
        st.caption("Ts-SD12 使用样本标准差（ddof=1）。本版本不提供正常参考值或诊断阈值。")
        st.markdown("### 模型含义")
        st.latex(r"L_i(t)=\exp\left[-\frac{(t-Ts_i)^2}{2\sigma^2}\right]")
        st.write("理想同步时，12 个亮点在 t=Ts 同时达到亮度 1。高斯函数仅用于可视化，不是真实心肌速度曲线。")
        if mode == "hold":
            st.write("保持模式：峰值前使用高斯亮度；t≥Ts 时亮度保持 1。")
        st.caption("已达峰计数按 t≥Ts 计算；闪烁结束后，计数仍为 12。")

    st.markdown("### 时间轴")
    st.write(f"当前时间 **{current} ms** · 使用左侧时间滑块，或点击以下按钮。")
    back, peak, forward = st.columns(3)
    back.button("后退 5 ms", on_click=step_time, args=(-5,), width="stretch")
    peak.button("跳到统一 Ts（同时最亮）", on_click=set_time_to_peak, width="stretch")
    forward.button("前进 5 ms", on_click=step_time, args=(5,), width="stretch")
    st.plotly_chart(create_timeline(ts, current, sigma, mode), use_container_width=True,
                    key="timeline", config={"displayModeBar": False})

    st.markdown("### 节段数据与导出")
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"当前亮度": st.column_config.NumberColumn(format="%.6f")})
    csv_col, png_col = st.columns(2)
    with csv_col:
        st.download_button("下载12节段 CSV", data=export_csv(values, current, sigma, mode),
                           file_name=f"lv12_Ts{ts}_t{current}_{mode}.csv", mime="text/csv",
                           width="stretch", on_click="ignore")
        st.caption("UTF-8 BOM 编码，可直接用 Excel 打开；包含当前时间、σ 和显示模式。")
    with png_col:
        st.write("**高清 PNG：点击上方牛眼图右上角的相机按钮。**")
        st.caption("浏览器直接导出 2000×2000 PNG，无需额外安装导出用浏览器。下方另提供可选 Kaleido 导出。")
        # 只在用户点击时生成图片，拖动时间滑块不会反复启动浏览器导出。
        signature = (ts, current, sigma, mode, show_names)
        cached = st.session_state.get("png_export")
        if cached is not None and cached[0] != signature:
            st.session_state.pop("png_export", None)
        if st.button("生成当前图的高清 PNG", help="可选的 Kaleido 导出；也可直接点击牛眼图相机按钮。", width="stretch"):
            try:
                with st.spinner("正在生成 2000×2000 PNG…"):
                    st.session_state.png_export = (signature, export_png(fig))
            except ImageExportError as exc:
                st.error("Kaleido PNG 导出失败；请使用牛眼图右上角相机按钮下载 PNG。")
                st.warning("本机 Chrome/Chromium 或浏览器策略可能影响 Kaleido。图形、CSV 和浏览器相机导出仍可使用；详见 README。")
                with st.expander("导出错误详情"):
                    st.text(str(exc))
        cached = st.session_state.get("png_export")
        if cached is not None:
            st.download_button("下载当前高清 PNG", data=cached[1],
                               file_name=f"lv12_Ts{ts}_t{current}_{mode}.png", mime="image/png",
                               width="stretch", on_click="ignore")
        st.caption("更改参数后，请重新生成 PNG，确保图片对应当前状态。")

    with st.expander("解剖映射、医学审核与版本范围"):
        st.warning(ANATOMY_REVIEW_STATUS)
        st.write("本图仅展示 17 节段命名体系中的基底段和中段，共 12 节段；不包含节段 13–17。")
        for view, numbers in APICAL_VIEW_SEGMENTS.items():
            st.write(f"切面预留接口 {APICAL_VIEW_LABELS[view]}：节段 {', '.join(map(str, numbers))}（待医学审核）")
        st.caption("预留映射用于后续切面绘图，本版本没有三切面图或切面旋转功能。来源及审核细节见 anatomy.py 和 README。")
        st.write("V0.1 不使用患者数据，不计算 SV、EF 或血流动力学。V1.0 可沿用现有计算接口接收不同的 Ts。")


if __name__ == "__main__":
    main()
