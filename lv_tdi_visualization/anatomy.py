"""左室基底段与中段的 12 节段解剖映射。

本模块只包含常用 AHA 17 节段体系中的 1～12 号，不包含 13～17 号
心尖段及心尖帽。不能把本模型称作完整的 17 节段模型。

坐标约定：使用通常的数学平面坐标，右方为 0°，上方为 90°。
牛眼图前壁在上、下壁在下、间隔在左、侧壁在右；1→6 和 7→12
分别逆时针排列。该约定是标准化示意图的显示方向，不能直接解释为
患者左右、探头方向或某个实际超声图像的屏幕方向。

医学审核说明：编号与名称采用用户指定的标准名单；牛眼方向及 A4C、
A2C、A3C 的节段对应采用常用映射。开发环境访问下列官方文献时返回
HTTP 403，因而未能逐图核对原文。这些解剖显示关系均应在用于课题、
教学或患者数据解释前由超声医师审核。测试只能证明代码映射一致，
不能代替医学审核。
"""

from dataclasses import dataclass
from numbers import Integral


@dataclass(frozen=True)
class Segment:
    """单个节段的固定属性；冻结数据避免滑块交互意外改变解剖位置。"""

    number: int
    name: str
    level: str
    wall: str
    center_angle_deg: float
    apical_view: str


# 每一行都显式给出编号与位置，避免按数组下标生成名称造成节段错配。
# 同一壁的基底与中段具有相同角度，仅其环形半径不同。
SEGMENTS: tuple[Segment, ...] = (
    Segment(1, "基底前壁", "基底段", "前壁", 90.0, "A2C"),
    Segment(2, "基底前间隔", "基底段", "前间隔", 150.0, "A3C"),
    Segment(3, "基底下间隔", "基底段", "下间隔", 210.0, "A4C"),
    Segment(4, "基底下壁", "基底段", "下壁", 270.0, "A2C"),
    Segment(5, "基底下侧壁", "基底段", "下侧壁", 330.0, "A3C"),
    Segment(6, "基底前侧壁", "基底段", "前侧壁", 30.0, "A4C"),
    Segment(7, "中段前壁", "中段", "前壁", 90.0, "A2C"),
    Segment(8, "中段前间隔", "中段", "前间隔", 150.0, "A3C"),
    Segment(9, "中段下间隔", "中段", "下间隔", 210.0, "A4C"),
    Segment(10, "中段下壁", "中段", "下壁", 270.0, "A2C"),
    Segment(11, "中段下侧壁", "中段", "下侧壁", 330.0, "A3C"),
    Segment(12, "中段前侧壁", "中段", "前侧壁", 30.0, "A4C"),
)


# 为未来三个心尖切面示意图保留接口。
# 元组包含基底与中段的节段集合，不规定未来切面图左右侧或行列顺序；
# 实际探头角度与切面偏转会改变所见室壁，因此不能视为个体图像配准。
APICAL_VIEW_SEGMENTS: dict[str, tuple[int, ...]] = {
    "A4C": (3, 9, 6, 12),  # 下间隔、前侧壁
    "A2C": (1, 7, 4, 10),  # 前壁、下壁
    "A3C": (2, 8, 5, 11),  # 前间隔、下侧壁
}

APICAL_VIEW_LABELS: dict[str, str] = {
    "A4C": "心尖四腔切面",
    "A2C": "心尖二腔切面",
    "A3C": "心尖三腔切面",
}

ANATOMY_REVIEW_STATUS = (
    "牛眼图方向及心尖四腔/二腔/三腔对应关系待医学审核："
    "本环境无法在线获取官方原文逐图核对。"
)

# 列出可供医学审核者核对的原始来源，不把链接可用性等同于已审核。
# 未核实的具体图号不填写，避免制造不准确的引用。
ANATOMY_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "title": (
            "Cerqueira et al. Standardized Myocardial Segmentation and "
            "Nomenclature for Tomographic Imaging of the Heart. "
            "Circulation. 2002;105:539–542."
        ),
        "doi": "10.1161/hc0402.102975",
        "url": "https://doi.org/10.1161/hc0402.102975",
        "review_status": "参考标准；本环境未能在线核实原文，具体图号待核对",
    },
    {
        "title": (
            "Lang et al. Recommendations for Cardiac Chamber Quantification "
            "by Echocardiography in Adults: An Update from ASE and EACVI. "
            "J Am Soc Echocardiogr. 2015;28:1–39.e14."
        ),
        "doi": "10.1016/j.echo.2014.10.003",
        "url": "https://doi.org/10.1016/j.echo.2014.10.003",
        "official_pdf": (
            "https://www.asecho.org/wp-content/uploads/2015/01/"
            "ChamberQuantification2015.pdf"
        ),
        "review_status": "参考标准；官方 PDF 访问返回 HTTP 403，具体图号待核对",
    },
)


def get_segment(number: int) -> Segment:
    """按标准编号取得节段；拒绝布尔值、非整数和超出 1～12 的编号。"""

    # bool 是 Python int 的子类，但 True/False 不能作为医学节段编号。
    if isinstance(number, bool) or not isinstance(number, Integral):
        raise TypeError("节段编号必须是 1～12 的整数。")
    if not 1 <= number <= 12:
        raise ValueError("节段编号必须在 1～12 范围内；本模型不包含心尖段。")
    return SEGMENTS[int(number) - 1]
