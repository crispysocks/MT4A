"""报告生成工具 — Agent 可调用的报告生成入口"""
from pathlib import Path
from typing import Optional

from app.agent.tools.registry import tool


REPORT_GENERATORS = {
    "daily_summary": ("app.reports.generators.daily_report_summary", "DailyReportSummaryGenerator"),
    "weekly_summary": ("app.reports.generators.daily_report_summary", "DailyReportSummaryGenerator"),
    "customer_analysis": ("app.reports.generators.customer_analysis", "CustomerAnalysisGenerator"),
    "psychology_weekly": ("app.reports.generators.psychology_weekly", "PsychologyWeeklyGenerator"),
    "complaint_weekly": ("app.reports.generators.complaint_weekly", "ComplaintWeeklyGenerator"),
}

REPORT_NAMES = {
    "daily_summary": "员工日报汇总报告",
    "weekly_summary": "员工日报汇总报告（周报）",
    "customer_analysis": "全域客户经营分析报告",
    "psychology_weekly": "学生心理健康周报",
    "complaint_weekly": "投诉处理周报",
}


@tool(
    "generate_report",
    "生成智能报告（docx格式），支持：员工日报、客户经营分析、心理健康周报、投诉处理周报",
    {
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "enum": ["daily_summary", "weekly_summary", "customer_analysis", "psychology_weekly", "complaint_weekly"],
                "description": "报告类型：daily_summary=员工日报，weekly_summary=员工周报，customer_analysis=客户经营分析，psychology_weekly=心理健康周报，complaint_weekly=投诉处理周报"
            },
            "period": {
                "type": "string",
                "enum": ["today", "yesterday", "this_week", "last_week"],
                "description": "时间周期：today=今天，yesterday=昨天，this_week=本周，last_week=上周"
            },
            "start_date": {
                "type": "string",
                "description": "自定义开始日期，格式：YYYY-MM-DD（可选）"
            },
            "end_date": {
                "type": "string",
                "description": "自定义结束日期，格式：YYYY-MM-DD（可选）"
            }
        },
        "required": ["report_type"],
    }
)
def generate_report(
    report_type: str,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    生成报告并保存为 docx 文件
    
    Args:
        report_type: 报告类型
        period: 时间周期（today/this_week/last_week 等）
        start_date: 自定义开始日期（YYYY-MM-DD）
        end_date: 自定义结束日期（YYYY-MM-DD）
    
    Returns:
        报告生成结果信息
    """
    from datetime import datetime
    import importlib
    
    # 验证报告类型
    if report_type not in REPORT_GENERATORS:
        return f"错误：不支持的报告类型 '{report_type}'。可用类型：{', '.join(REPORT_GENERATORS.keys())}"
    
    # 默认周期
    if period is None:
        period = "today" if report_type in ("daily_summary",) else "this_week"
    
    # 解析自定义日期
    parsed_start = None
    parsed_end = None
    if start_date:
        try:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return f"错误：开始日期格式错误，应为 YYYY-MM-DD"
    if end_date:
        try:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return f"错误：结束日期格式错误，应为 YYYY-MM-DD"
    
    # 动态导入生成器类
    module_path, class_name = REPORT_GENERATORS[report_type]
    module = importlib.import_module(module_path)
    generator_class = getattr(module, class_name)
    
    # 创建生成器并生成报告
    try:
        generator = generator_class(
            period=period,
            start_date=parsed_start,
            end_date=parsed_end,
        )
        filepath = generator.generate()
        
        report_name = REPORT_NAMES.get(report_type, report_type)
        return (
            f"✅ 报告已生成完成！\n"
            f"📄 报告名称：{report_name}\n"
            f"📁 文件路径：{filepath}\n"
            f"📥 可直接下载查看"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ 报告生成失败：{e}"
