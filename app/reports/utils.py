"""报告生成通用工具函数"""
from datetime import datetime, timedelta
from typing import Tuple


def get_date_range(period: str) -> Tuple[datetime, datetime]:
    """
    根据周期获取日期范围
    
    Args:
        period: 时间周期标识
            - "today": 今天
            - "yesterday": 昨天
            - "this_week": 本周（周一到周日）
            - "last_week": 上周
        
    Returns:
        (start_date, end_date) 元组
    """
    now = datetime.now()
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "this_week":
        # 本周一
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "last_week":
        # 上周一到上周日
        last_monday = now - timedelta(days=now.weekday() + 7)
        start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = (last_monday + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # 默认本周
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    
    return start, end


def calc_yoy_change(current: float, previous: float) -> str:
    """
    计算同比/环比变化率
    
    Args:
        current: 当前期数值
        previous: 上期数值
        
    Returns:
        变化率字符串，如 "+15.3%" 或 "-8.2%"
    """
    if previous == 0:
        return "N/A" if current == 0 else "+∞"
    
    change = ((current - previous) / previous) * 100
    return f"{change:+.1f}%"


def format_period_label(period: str) -> str:
    """
    格式化周期标签为中文显示
    
    Args:
        period: 周期标识
        
    Returns:
        中文标签
    """
    labels = {
        "today": "今日",
        "yesterday": "昨日",
        "this_week": "本周",
        "last_week": "上周",
    }
    return labels.get(period, period)


def get_week_number(dt: datetime = None) -> str:
    """获取ISO周数，如 '2026年第20周'"""
    dt = dt or datetime.now()
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}年第{iso_week}周"
