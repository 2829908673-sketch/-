# 左心室12节段收缩峰值时序可视化系统 V0.1

**基于组织多普勒峰值时间的简化数字化模型**

这是一个可以运行的 Python + Streamlit 演示程序，用于课题《基于组织多普勒的左心室12节段收缩峰值时序空间可视化及泵血功能关联研究》的第一阶段。无需真实患者数据：12 个节段共用一个峰值时间 Ts，拖动时间滑块即可观察它们在同一时刻达到最大显示亮度。

**亮起只表示到达预设的组织多普勒收缩期速度峰值时间 Ts，不表示心肌电激动、真实收缩开始、收缩幅度或收缩力。默认 Ts=300 ms 只是程序演示参数，不是正常人群参考值。高斯亮度函数不是真实心肌速度曲线。**

本图只展示常用左室 17 节段命名体系中的基底段和中段，共 12 节段；不包含心尖段 13～16 或心尖帽 17，不是完整的 17 节段牛眼图。本版本没有正常值、诊断阈值、SV、EF 或血流动力学计算。

## 1. 文件与功能

```text
lv_tdi_visualization/
├── app.py                       # 中文网页界面、参数、数据表和下载按钮
├── anatomy.py                   # 12节段编号、名称、固定位置和切面预留接口
├── timing.py                    # Ts校验、亮度、时序指标、表格和CSV
├── visualization.py             # Plotly牛眼图、时间轴、PNG导出
├── requirements.txt             # 固定依赖版本
├── README.md                    # 本说明
└── tests/
    ├── conftest.py              # 测试导入路径设置
    ├── test_timing.py           # 数学计算、非法输入、CSV与同步更新测试
    ├── test_anatomy.py          # 编号、名称、固定位置、切面接口完整性测试
    ├── test_visualization.py    # 图形数据绑定、位置与导出错误处理测试
    └── test_app.py              # Streamlit界面、滑块、按钮、重置测试
```

程序采用免费的开源工具：Streamlit、NumPy、Plotly、pandas、pytest；Kaleido 提供另一种可选的 PNG 导出方式。无需 QLAB、MATLAB 或商业 CFD 软件。

## 2. 第一次安装：Windows

建议安装 **Python 3.11 或 3.12**，下载地址为 <https://www.python.org/downloads/>。本项目已在 Python 3.12.14 验证；代码使用 Python 3.11 兼容语法。安装时保留 Python Launcher，并勾选将 Python 加入 PATH 的选项。

在资源管理器打开 `lv_tdi_visualization` 文件夹，在地址栏输入 `powershell` 后按回车。下面的命令都要在这个文件夹内运行，不是在它的上级目录。

先检查 Python：

```powershell
py -3 --version
```

创建独立环境并安装依赖：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

这里直接调用独立环境中的 Python，**不需要运行 activate**，也不需要修改 PowerShell 的脚本执行策略。如果电脑装了多个 Python 版本，可将第一条创建环境命令中的 `py -3` 改为 `py -3.11` 或 `py -3.12`。

运行测试并启动网页：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

终端会显示本机访问地址，并通常自动打开浏览器。如果没有自动打开，复制终端给出的本机地址到自己的浏览器。保持这个终端窗口开启；按 `Ctrl+C` 停止程序。

## 3. 第一次安装：macOS / Linux

安装 Python 3.11 或 3.12 后打开终端，进入项目文件夹。请将下面示例路径换成你实际存放文件的位置：

```bash
cd /你的实际路径/lv_tdi_visualization
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m streamlit run app.py
```

同样无需激活环境。若 `python3` 指向其他版本，可在创建环境时使用已安装的 `python3.11` 或 `python3.12`。Linux 如提示缺少 `venv`，请先安装系统对应版本的 Python venv 组件，再重新创建环境。

终端会显示本机访问地址；在自己的浏览器打开即可。按 `Ctrl+C` 停止程序。

## 4. 以后如何启动

无需重复创建环境或安装依赖。打开终端，进入 `lv_tdi_visualization` 文件夹，只运行对应系统的启动命令：

Windows：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux：

```bash
.venv/bin/python -m streamlit run app.py
```

## 5. 如何操作

1. 页面首次打开时，统一 Ts 为 **300 ms**，当前 t 为 **0 ms**，σ 为 **15 ms**，显示模式为“瞬时闪烁”。12 个亮点接近浅灰色。
2. 在左侧拖动“当前时间 t”到 **300 ms**，或点击“跳到统一 Ts（同时最亮）”。12 个亮点同时变为最亮的橙黄色，当前亮度均为 1，已达峰数量为 12/12。
3. 继续增大 t，瞬时闪烁模式的亮点逐渐变回浅灰色；已达峰计数仍为 12/12，因为它表示曾经到达 Ts。
4. 调整“统一峰值时间 Ts”，全部 12 节段的 Ts 一起改变。点击“跳到统一 Ts”再次查看新的同步峰值。
5. 调整 σ 观察亮点变亮、变暗的显示宽度。σ 不是心肌真实收缩持续时间，也不是一个绝对的亮起起止区间。
6. 选择“到达后保持高亮”，峰值前仍使用高斯亮度，达到 Ts 后保持亮度 1。它只是方便展示的另一种显示规则。
7. 可点击“后退 5 ms”“前进 5 ms”细看变化。时间限制在 0～600 ms 内。
8. 鼠标悬停在编号亮点上可查看节段编号、中文名称、Ts、当前时间和亮度；左侧可关闭中文名称以简化图面。
9. 点击“重置参数”恢复初始设置。它同时清除旧的 Kaleido PNG 缓存，避免下载参数已变化前的图片。

| 参数 | 范围 | 初始值 | 含义 |
| --- | --- | --- | --- |
| 统一峰值时间 Ts | 100～500 ms | 300 ms | 12 个节段共用的演示峰值时间 |
| 当前时间 t | 0～600 ms | 0 ms | 全局显示时间 |
| 亮点持续宽度 σ | 5～50 ms | 15 ms | 高斯显示宽度参数 |
| 显示模式 | 瞬时闪烁 / 到达后保持高亮 | 瞬时闪烁 | 数学显示规则 |

主图外环是基底段 1～6，内环是中段 7～12。几何位置固定，滑块只改变亮度和数值。下方时间轴展示 12 条重合亮度曲线中的一条，蓝色线和点表示当前时间。

本版本优先提供稳定的手动时间滑块和步进按钮，没有自动播放或暂停功能，不依赖自动刷新插件。

## 6. 数学定义与结果解释

理想同步模式使用：

```text
Ts₁ = Ts₂ = … = Ts₁₂ = T₀
Lᵢ(t) = exp[-(t - Tsᵢ)² / (2σ²)]
```

瞬时闪烁模式中，`t=Tsᵢ` 时 `Lᵢ=1`；远离峰值时亮度接近 0。保持模式在 `t<Tsᵢ` 时使用同一高斯函数，在 `t≥Tsᵢ` 时使用 `Lᵢ=1`。亮点的灰色到橙黄色按亮度连续插值。

亮度会在 Ts 前逐渐升高，这来自高斯显示算法，**不意味着该节段已经到达真实峰值**。数据表中的“是否已经达到峰值”及结果区的计数均严格按 `t≥Tsᵢ` 判断，不按颜色或亮度阈值判断。

结果区计算 Ts 平均值、Ts-SD12、最大节段时间差、最早及最晚峰值时间。本软件明确使用**样本标准差**：

```text
Ts-SD12 = sqrt[Σ(Tsᵢ - Ts平均值)² / (12 - 1)]
最大节段时间差 = max(Tsᵢ) - min(Tsᵢ)
```

理想同步时，Ts-SD12 和最大节段时间差都严格为 **0 ms**。该样本标准差约定应在未来患者研究方案中复核。本版本不设置正常人群参考值或不同步诊断阈值。

时间输入必须是有限非负实数，σ 必须大于 0，Ts 向量必须恰有 12 个值；非法输入会给出明确错误。界面的范围是演示操作限制，计算函数本身可接受范围更广的合法时间。

## 7. 导出图片与 CSV

### 推荐的 PNG 导出：主图相机按钮

点击**牛眼图右上角的相机按钮**，浏览器会直接下载当前状态的 **2000×2000 PNG**，适合插入开题 PPT。文件名包含统一 Ts、当前 t 和显示模式，例如 `lv12_Ts300_t300_flash.png`。

这种方式由正在显示网页的浏览器完成，**不需要在 Python 运行环境中额外安装 Chrome、Chromium 或配置 Kaleido**。导出前先调到希望展示的时刻；鼠标相机按钮只属于主牛眼图，下方时间轴没有相机按钮。

### CSV 导出

点击“下载12节段 CSV”。文件采用 **UTF-8 BOM** 编码，可用 Windows Excel 直接打开中文。含表头及 **12 条节段记录**，列为：

- 节段编号、中文名称、Ts (ms)。
- 当前时间 t (ms)、σ (ms)、显示模式。
- 当前亮度、是否已经达到峰值。

CSV 保存的是点击下载时的状态。更改参数后重新下载即可。

### 另一种 PNG 导出：Kaleido 按钮

页面另外提供“生成当前图的高清 PNG”及生成后的“下载当前高清 PNG”。`requirements.txt` 固定了配套版本 **Plotly 6.3.1 + Kaleido 1.1.0**。Kaleido 1.x 还需要运行 Python 的机器已经安装 Google Chrome 或 Chromium，且其浏览器策略允许 Kaleido 打开临时本地页面。

如果浏览器安装在非默认位置，可在启动 Streamlit 前设置 `BROWSER_PATH` 为浏览器可执行文件的实际路径。例如 Windows：

```powershell
$env:BROWSER_PATH = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS 的常见 Chrome 路径示例：

```bash
export BROWSER_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
.venv/bin/python -m streamlit run app.py
```

路径示例不表示你的电脑一定装在这个位置，请按实际安装情况使用。

**当前云环境的管理员浏览器策略禁止 `file://` 临时页面，Kaleido 导出出现 `kaleido_scopes` 未定义错误。已定位原因，未修改管理策略。** 如遇类似错误，直接使用主图相机导出。界面会显示可展开的导出错误详情，不影响计算、图形、CSV 或相机 PNG 下载。

更改 Ts、t、σ、显示方式或名称显示后，旧的 Kaleido PNG 会失效，必须重新生成。相机按钮始终导出当前主图。

## 8. 解剖映射及医学审核

编号与中文名称按用户指定的常用 AHA 17 节段命名体系列出：

| 编号 | 中文名称 | 层级 | 扇形中心角度 |
| --- | --- | --- | --- |
| 1 | 基底前壁 | 基底段 | 90° |
| 2 | 基底前间隔 | 基底段 | 150° |
| 3 | 基底下间隔 | 基底段 | 210° |
| 4 | 基底下壁 | 基底段 | 270° |
| 5 | 基底下侧壁 | 基底段 | 330° |
| 6 | 基底前侧壁 | 基底段 | 30° |
| 7 | 中段前壁 | 中段 | 90° |
| 8 | 中段前间隔 | 中段 | 150° |
| 9 | 中段下间隔 | 中段 | 210° |
| 10 | 中段下壁 | 中段 | 270° |
| 11 | 中段下侧壁 | 中段 | 330° |
| 12 | 中段前侧壁 | 中段 | 30° |

程序使用数学坐标：右方 0°，上方 90°。显示约定为**前壁在上、下壁在下、间隔在左、侧壁在右**；每一环按 1→6 或 7→12 逆时针排列。这是牛眼示意图的方向约定，不能直接当作患者左右、探头方向或实际超声图像的屏幕方向。

预留的三个心尖切面接口采用以下常用对应：

| 接口 | 切面 | 一侧节段 | 另一侧节段 | 审核状态 |
| --- | --- | --- | --- | --- |
| A4C | 心尖四腔 | 下间隔 3、9 | 前侧壁 6、12 | 待医学审核 |
| A2C | 心尖二腔 | 前壁 1、7 | 下壁 4、10 | 待医学审核 |
| A3C | 心尖三腔 | 前间隔 2、8 | 下侧壁 5、11 | 待医学审核 |

此表表示节段集合，不规定未来切面图的屏幕左右顺序。真实切面中的探头角度、偏转及患者结构差异需要另外审核，接口不是个体图像配准。V0.1 还没有三切面绘图。

**牛眼圆周方向和 A4C/A2C/A3C 对应均标记为待医学审核。** 本次开发环境访问 ASE、ESC/EACVI、PubMed 和 OUP 官方文献来源时返回 HTTP 403，无法取得原文逐图核实。因此未编造图号，也不将来源链接视作已完成核实。请在用于课题报告、教学或患者解释前由超声医师核对以下标准和实际切面，并审核本代码中的映射。

可供审核的原始标准：

1. Cerqueira et al. *Standardized Myocardial Segmentation and Nomenclature for Tomographic Imaging of the Heart.* Circulation. 2002;105:539–542. DOI：[10.1161/hc0402.102975](https://doi.org/10.1161/hc0402.102975)。
2. Lang et al. *Recommendations for Cardiac Chamber Quantification by Echocardiography in Adults: An Update from ASE and EACVI.* J Am Soc Echocardiogr. 2015;28:1–39.e14. DOI：[10.1016/j.echo.2014.10.003](https://doi.org/10.1016/j.echo.2014.10.003)。[ASE 官方 PDF](https://www.asecho.org/wp-content/uploads/2015/01/ChamberQuantification2015.pdf)。

解剖自动化测试验证编号、名称、角度与接口的一致性，**不能替代医学审核或证明标准来源已经核实**。

## 9. 测试与已验证范围

在云环境 Python 3.12.14 上，`python -m pytest -q` 的结果为 **79 passed**。测试覆盖用户要求的同步标准差与最大时间差为 0、峰值亮度为 1、远离峰值亮度接近 0、完整编号与名称、非法输入报错、CSV 含 12 条节段、统一 Ts 改变后的同步更新，以及补充的界面和图形检查。

已实际启动 Streamlit，默认页面和峰值页面可加载。真实 Chromium 浏览器自动化检查了“跳到统一 Ts”后 12 个节段亮度均为 1、颜色均为橙黄色，并成功操作主图相机 PNG 下载和 CSV 下载按钮。

已解析实际下载文件：PNG 为 **2000×2000**；CSV 为 **12 条记录**，峰值演示时全部 Ts=300 ms、亮度=1、已达峰标记为真。中文标签及节段布局也已检查。

自动化测试同时检查了 Streamlit 控件、保持模式、重置和步进行为。**尚未在用户自己的 Windows 或 macOS 上人工操作验收，也未完成原始文献逐图医学审核。** Kaleido 在当前云环境受到上文所述浏览器策略限制；推荐相机导出已通过浏览器操作验证。

可随时在项目文件夹用独立环境再次运行测试：

```text
Windows：.\.venv\Scripts\python.exe -m pytest -q
macOS/Linux：.venv/bin/python -m pytest -q
```

## 10. 常见问题

- **提示找不到 app.py 或 requirements.txt：** 当前终端没有进入 `lv_tdi_visualization`。先进入这个文件夹，再执行命令。
- **提示 `No module named streamlit` 等：** 使用独立环境的 Python 安装与启动，避免使用另一个 Python 环境。重新执行对应系统的依赖安装命令。
- **端口被占用：** 在启动命令末尾加 `--server.port 8502`，然后按终端新显示的地址访问。
- **中文显示方框：** 浏览器所在系统需要中文字体。Windows/macOS 通常已有；Linux 可安装 Noto Sans CJK 字体后重启应用或浏览器。
- **t 大于 Ts 后亮点变灰但计数仍为 12：** 瞬时闪烁模式亮度会回落，而计数记录 `t≥Ts`，两者含义不同；改用保持模式即可保留高亮。
- **PNG 生成按钮报错：** 优先点击牛眼图相机按钮。Kaleido 是另一条导出路径，需要系统浏览器和可用的浏览器策略。
- **没有出现浏览器窗口：** 保持终端运行，手动把终端给出的本机地址复制到浏览器打开。

## 11. 已预留接口与下一步 V1.0

`timing.py` 中的 `validate_ts`、`compute_metrics`、`calculate_brightness`、`build_segment_table`、`export_csv` 和 `visualization.py` 中的 `create_bullseye` 已支持**按节段编号 1～12 排列的 12 个不同 Ts**。V0.1 界面只调用 `uniform_ts`，不开放患者输入。

未来接收 12 个不同 Ts 的计算示例仅用于说明接口，不会自动改变本版界面：

```python
from timing import compute_metrics, calculate_brightness

ts_ms = [280, 295, 310, 305, 290, 300, 285, 300, 315, 310, 295, 305]
metrics = compute_metrics(ts_ms)
brightness = calculate_brightness(ts_ms, t_ms=300, sigma_ms=15)
```

升级 V1.0 的顺序建议为：先完成医学审核和研究测量规范，明确 ECG/QRS 时间零点、毫秒单位、收缩期速度峰值识别、可测量性、心搏选取及重复测量规则；再添加按固定编号输入 12 个 Ts 的表格或 CSV 入口，校验缺失、重复、无效时间；最后将同一 Ts 向量接入现有指标、牛眼图和导出函数，增加不同步数据的界面测试。研究方案应明确如何处理无法可靠测量的节段，不自动编造其 Ts。

`anatomy.py` 的 `APICAL_VIEW_SEGMENTS` 与 `APICAL_VIEW_LABELS` 留给未来三切面图；先完成映射审核再扩展可视化。

后续 V2.0 可研究空间时序特征及左室结构参数与泵血功能的关联；V3.0 可探索参数化室壁运动和简化血流动力学。当前版本没有提前实现这些预测或模拟功能。
