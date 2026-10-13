"""验证映射完整性及坐标一致性；这些测试不替代医师对解剖的审核。"""

import pytest

from anatomy import APICAL_VIEW_SEGMENTS, SEGMENTS, get_segment


EXPECTED_NAMES = (
    "基底前壁",
    "基底前间隔",
    "基底下间隔",
    "基底下壁",
    "基底下侧壁",
    "基底前侧壁",
    "中段前壁",
    "中段前间隔",
    "中段下间隔",
    "中段下壁",
    "中段下侧壁",
    "中段前侧壁",
)


def test_numbers_are_unique_and_complete():
    """必须恰有 1～12 号，不能漏号、重复或混入心尖段。"""
    numbers = [segment.number for segment in SEGMENTS]
    assert numbers == list(range(1, 13))
    assert len(set(numbers)) == 12


def test_names_match_numbers_one_to_one():
    """逐一与指定标准名单比较，防止编号与名称错配。"""
    assert tuple(segment.name for segment in SEGMENTS) == EXPECTED_NAMES
    for number, name in enumerate(EXPECTED_NAMES, start=1):
        assert get_segment(number).name == name


def test_same_wall_has_same_angle_in_both_rings():
    """同一壁上下两个层级应在同一径向，保证牛眼图不会错位。"""
    expected_angles = (90.0, 150.0, 210.0, 270.0, 330.0, 30.0)
    for index, expected_angle in enumerate(expected_angles):
        basal, middle = SEGMENTS[index], SEGMENTS[index + 6]
        assert basal.level == "基底段"
        assert middle.level == "中段"
        assert basal.wall == middle.wall
        assert basal.center_angle_deg == middle.center_angle_deg == expected_angle


def test_apical_view_interface_covers_each_shown_segment_once():
    """核对预留切面接口与节段属性一致；不声称验证了临床切面。"""
    all_numbers = []
    for view, numbers in APICAL_VIEW_SEGMENTS.items():
        assert len(numbers) == 4
        all_numbers.extend(numbers)
        assert all(get_segment(number).apical_view == view for number in numbers)
    assert sorted(all_numbers) == list(range(1, 13))


@pytest.mark.parametrize("number", [0, -1, 13, 17, 100])
def test_out_of_range_segment_rejected(number):
    with pytest.raises(ValueError, match="1～12"):
        get_segment(number)


@pytest.mark.parametrize("number", [True, False, 1.0, "1", None])
def test_noninteger_segment_rejected(number):
    with pytest.raises(TypeError, match="整数"):
        get_segment(number)
