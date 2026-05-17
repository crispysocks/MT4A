from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Course(SQLModel, table=True):
    """课程与项目表 - 支撑客服Agent的课程推荐功能"""
    __tablename__ = "courses"
    __table_args__ = {"comment": "课程与项目表，支撑课程推荐和留学方案匹配"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "课程ID"})
    name: str = Field(sa_column_kwargs={"comment": "课程名称"})
    type: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "课程类型（如：语言课程、背景提升）"})
    country: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "目标国家/地区"})
    recruitment_group: Optional[str] = Field(default=None, max_length=255, sa_column_kwargs={"comment": "招生群体"})
    duration: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "课程时长"})
    fees: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "费用说明"})
    features: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "课程特色"})
    certification: Optional[str] = Field(default=None, max_length=255, sa_column_kwargs={"comment": "证书/认证"})
    allowance: Optional[str] = Field(default=None, max_length=255, sa_column_kwargs={"comment": "奖学金信息"})
    description: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "课程描述"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "创建时间"})
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "更新时间"})


class Event(SQLModel, table=True):
    """活动与讲座表 - 支撑活动查询和报名闭环"""
    __tablename__ = "events"
    __table_args__ = {"comment": "活动与讲座表，支撑留学分享会、招生官见面会等活动管理"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "活动ID"})
    name: str = Field(sa_column_kwargs={"comment": "活动名称"})
    type: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "活动类型（如：线上分享会、线下见面会）"})
    event_datetime: Optional[datetime] = Field(default=None, sa_column_kwargs={"comment": "活动日期时间"})
    location: Optional[str] = Field(default=None, max_length=255, sa_column_kwargs={"comment": "活动地点"})
    description: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "活动描述"})
    status: Optional[str] = Field(default="active", max_length=50, sa_column_kwargs={"comment": "活动状态（active/closed）"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "创建时间"})
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "更新时间"})


class Registration(SQLModel, table=True):
    """活动报名表 - 记录客户活动预约报名信息"""
    __tablename__ = "registrations"
    __table_args__ = {"comment": "活动报名表，沉淀私域流量，记录活动预约信息"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "报名ID"})
    event_id: int = Field(foreign_key="events.id", sa_column_kwargs={"comment": "关联活动ID"})
    name: str = Field(max_length=100, sa_column_kwargs={"comment": "报名人姓名"})
    phone: str = Field(max_length=50, sa_column_kwargs={"comment": "报名人电话"})
    email: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "报名人邮箱"})
    country_interest: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "意向国家"})
    education: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "学历背景"})
    notes: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "备注信息"})
    registration_date: Optional[datetime] = Field(default_factory=datetime.now, sa_column_kwargs={"comment": "报名时间"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "创建时间"})


class User(SQLModel, table=True):
    """用户表 - 员工和学生统一用户管理"""
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表，统一管理员工和学生账户"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "用户ID"})
    username: str = Field(max_length=50, unique=True, index=True, sa_column_kwargs={"comment": "用户名"})
    password_hash: str = Field(max_length=255, sa_column_kwargs={"comment": "密码哈希"})
    role: str = Field(max_length=20, sa_column_kwargs={"comment": "角色（employee/student/guest）"})
    class_advisor_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True, sa_column_kwargs={"comment": "班主任/顾问ID"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "创建时间"})


class Lead(SQLModel, table=True):
    """意向客户表 - CRM核心，支撑企业智能助手的客户管理"""
    __tablename__ = "leads"
    __table_args__ = {"comment": "意向客户表，支撑企业智能助手的客户录入、状态更新和跟进记录查询"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "客户ID"})
    name: str = Field(max_length=100, sa_column_kwargs={"comment": "客户姓名"})
    phone: Optional[str] = Field(default=None, max_length=50, sa_column_kwargs={"comment": "客户电话"})
    email: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "客户邮箱"})
    source: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "客户来源渠道"})
    status: Optional[str] = Field(default="new", max_length=50, sa_column_kwargs={"comment": "客户状态（new/contacted/negotiating/signed/lost）"})
    assigned_to: Optional[int] = Field(default=None, foreign_key="users.id", sa_column_kwargs={"comment": "负责员工ID"})
    notes: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "客户备注信息"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "创建时间"})
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"onupdate": lambda: datetime.now(), "comment": "更新时间"})


class LeadFollowUp(SQLModel, table=True):
    """意向客户跟进记录表 - 支撑员工查询客户历史跟进记录"""
    __tablename__ = "lead_follow_ups"
    __table_args__ = {"comment": "意向客户跟进记录表，记录员工与客户的每次沟通详情"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "跟进记录ID"})
    lead_id: int = Field(foreign_key="leads.id", sa_column_kwargs={"comment": "关联客户ID"})
    content: str = Field(sa_column_kwargs={"comment": "跟进内容"})
    follow_type: Optional[str] = Field(default=None, max_length=50, sa_column_kwargs={"comment": "跟进方式（如：电话/微信/拜访）"})
    created_by: Optional[int] = Field(default=None, foreign_key="users.id", sa_column_kwargs={"comment": "跟进人ID"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "跟进时间"})


class DailyReport(SQLModel, table=True):
    """员工日报表 - 支撑口述日报和管理日报查阅"""
    __tablename__ = "daily_reports"
    __table_args__ = {"comment": "员工日报表，支撑企业智能助手的口述日报和管理日报查阅功能"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "日报ID"})
    user_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "提交人ID"})
    content: str = Field(sa_column_kwargs={"comment": "日报内容（原始口述或结构化文本）"})
    summary: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "AI提取的摘要"})
    department: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "所属部门"})
    submitted_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "提交时间"})


class Complaint(SQLModel, table=True):
    """投诉反馈表 - 支撑售后反馈和投诉处理周报"""
    __tablename__ = "complaints"
    __table_args__ = {"comment": "投诉反馈表，支撑学生售后反馈、老师跟进处理及投诉处理周报"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "投诉ID"})
    student_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "投诉学生ID"})
    category: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "投诉类别（如：签证办理/院校申请/生活服务）"})
    content: str = Field(sa_column_kwargs={"comment": "投诉详细内容"})
    status: Optional[str] = Field(default="pending", max_length=50, sa_column_kwargs={"comment": "处理状态（pending/processing/resolved）"})
    handler_id: Optional[int] = Field(default=None, foreign_key="users.id", sa_column_kwargs={"comment": "处理人ID"})
    resolution: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "解决方案"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "投诉时间"})
    resolved_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"comment": "解决时间"})


class Organization(SQLModel, table=True):
    """组织架构表 - 支撑组织架构查询和新人入职指引"""
    __tablename__ = "organization"
    __table_args__ = {"comment": "组织架构表，支撑企业智能助手的组织架构查询功能"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "部门ID"})
    name: str = Field(max_length=100, sa_column_kwargs={"comment": "部门名称"})
    org_type: str = Field(max_length=50, sa_column_kwargs={"comment": "部门类型"})
    parent_id: Optional[int] = Field(default=None, foreign_key="organization.id", sa_column_kwargs={"comment": "上级部门ID"})
    contact_info: Optional[str] = Field(default=None, max_length=255, sa_column_kwargs={"comment": "联系方式"})


class StudentGrade(SQLModel, table=True):
    """学生成绩表 - 支撑学生成绩录入与查询"""
    __tablename__ = "student_grades"
    __table_args__ = {"comment": "学生成绩表，支撑企业智能助手的学生成绩管理功能"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "成绩记录ID"})
    student_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "学生ID"})
    subject: str = Field(max_length=100, sa_column_kwargs={"comment": "科目"})
    grade: Optional[str] = Field(default=None, max_length=20, sa_column_kwargs={"comment": "成绩"})
    semester: Optional[str] = Field(default=None, max_length=50, sa_column_kwargs={"comment": "学期"})
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "记录时间"})


class LeaveRequest(SQLModel, table=True):
    """请假申请表 - 支撑学生请假申请和审批闭环"""
    __tablename__ = "leave_requests"
    __table_args__ = {"comment": "请假申请表，支撑学生在线提交请假、班主任推送及移动端审批的完整闭环"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "请假申请ID"})
    student_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "申请人学生ID"})
    reason: str = Field(sa_column_kwargs={"comment": "请假原因"})
    start_date: str = Field(sa_column_kwargs={"comment": "开始日期"})
    end_date: str = Field(sa_column_kwargs={"comment": "结束日期"})
    status: Optional[str] = Field(default="pending", max_length=50, sa_column_kwargs={"comment": "审批状态（pending/approved/rejected）"})
    approver_id: Optional[int] = Field(default=None, foreign_key="users.id", sa_column_kwargs={"comment": "审批人ID（班主任）"})
    approved_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"comment": "审批时间"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "提交时间"})


class ExamSchedule(SQLModel, table=True):
    """考试安排表 - 支撑学业考务和智能提醒"""
    __tablename__ = "exam_schedule"
    __table_args__ = {"comment": "考试安排表，支撑学生查询论文DDL、考试时间及智能提醒功能"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "考试安排ID"})
    student_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "学生ID"})
    exam_type: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "考试类型（如：论文、考试）"})
    subject: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "科目/论文题目"})
    deadline: Optional[datetime] = Field(default=None, sa_column_kwargs={"comment": "截止时间/DDL"})
    description: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "考试说明"})


class PsychologyProfile(SQLModel, table=True):
    """心理健康画像表 - 支撑心理关怀和心理健康周报"""
    __tablename__ = "psychology_profiles"
    __table_args__ = {"comment": "心理健康画像表，支撑学生智能助手日常情绪打卡和心理健康周报分析"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "画像记录ID"})
    student_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "学生ID"})
    emotion_tag: Optional[str] = Field(default=None, max_length=100, sa_column_kwargs={"comment": "情绪标签（如：焦虑/孤独/压力）"})
    score: Optional[int] = Field(default=None, sa_column_kwargs={"comment": "情绪评分（1-100）"})
    notes: Optional[str] = Field(default=None, sa_column_kwargs={"comment": "备注说明"})
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "记录时间"})


class PsychologyWarning(SQLModel, table=True):
    """心理预警表 - 支撑高危风险预警和老师介入干预"""
    __tablename__ = "psychology_warnings"
    __table_args__ = {"comment": "心理预警表，实时监测学生心理状态，触发高危预警并通知老师介入"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "预警记录ID"})
    student_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "学生ID"})
    trigger_reason: str = Field(sa_column_kwargs={"comment": "触发原因"})
    risk_level: Optional[str] = Field(default="medium", max_length=50, sa_column_kwargs={"comment": "风险等级（low/medium/high）"})
    status: Optional[str] = Field(default="active", max_length=50, sa_column_kwargs={"comment": "处理状态（active/handled）"})
    handler_id: Optional[int] = Field(default=None, foreign_key="users.id", sa_column_kwargs={"comment": "处理老师ID"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "预警时间"})


class Notification(SQLModel, table=True):
    """通知消息表 - 支撑审批回调和投诉解决通知"""
    __tablename__ = "notifications"
    __table_args__ = {"comment": "通知消息表，支撑请假审批回调、投诉解决自动通知等消息推送功能"}

    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"comment": "通知ID"})
    user_id: int = Field(foreign_key="users.id", sa_column_kwargs={"comment": "接收用户ID"})
    notification_type: str = Field(max_length=50, sa_column_kwargs={"comment": "通知类型（如：leave_request/complaint）"})
    status: Optional[str] = Field(default="active", max_length=50, sa_column_kwargs={"comment": "通知状态（active/read）"})
    operation_type: str = Field(max_length=50, sa_column_kwargs={"comment": "操作类型（如：approved/resolved）"})
    content_summary: str = Field(sa_column_kwargs={"comment": "通知内容摘要"})
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "创建时间"})
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(), sa_column_kwargs={"comment": "更新时间"})