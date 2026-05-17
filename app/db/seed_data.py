"""
Database seed data initialization.
All default data is sourced from knowledge/raw/ documents.
"""
import bcrypt
from sqlmodel import Session, select
from app.db.connection import engine
from app.db.models import (
    Course, Event, Organization, User,
)


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _seed_organizations(session: Session):
    """Source: knowledge/raw/公司信息/企业信息.md - 部门架构"""
    orgs = [
        {"name": "广东省教育服务有限公司", "org_type": "company", "parent_id": None, "contact_info": "020-37628058"},
        {"name": "双元制事业部", "org_type": "department", "parent_id": 1, "contact_info": "专注于德国双元制教育模式的深入探索与推广实践"},
        {"name": "智能装备事业部", "org_type": "department", "parent_id": 1, "contact_info": "智慧校园/AI助教/新能源基础设施建设"},
        {"name": "课后服务事业部", "org_type": "department", "parent_id": 1, "contact_info": "专注双减政策落地与素质教育延伸"},
        {"name": "研学服务事业部", "org_type": "department", "parent_id": 1, "contact_info": "链接课堂知识与真实世界的实践平台"},
        {"name": "科技赛事事业部", "org_type": "department", "parent_id": 1, "contact_info": "赋能青少年科技创新能力培养"},
    ]
    for org_data in orgs:
        existing = session.exec(select(Organization).where(Organization.name == org_data["name"])).first()
        if not existing:
            org = Organization(**org_data)
            session.add(org)


def _seed_courses(session: Session):
    """
    Germany courses source: knowledge/raw/公司业务/中德精英人才共建计划.md
    Singapore courses source: knowledge/raw/公司业务/新加坡国际本硕升学计划.md
    """
    courses = [
        # Germany dual-system courses
        {
            "name": "德国双元制职业培训项目",
            "type": "双元制",
            "country": "德国",
            "recruitment_group": "18-35岁，高中及以上学历",
            "duration": "2-3.5年",
            "fees": "免学费，企业每月发放酬金",
            "features": "省属教育国企直接签协议；银行全额低息贷款；国内外全程保姆式服务",
            "certification": "IHK/HWK职业资格证书",
            "allowance": "机电一体化专业：第一年880欧/月，第二年950欧/月，第三年1030欧/月",
            "description": "受训者需在职业学校和企业两个场所培训，每周3-4天在企业学习实践技能，8-12课时理论课程。培训费用由企业和国家共同承担。",
        },
        {
            "name": "德国医疗健康类培训",
            "type": "双元制",
            "country": "德国",
            "recruitment_group": "18-35岁，高中及以上学历",
            "duration": "2-3.5年",
            "fees": "免学费",
            "features": "省属教育国企直接签协议；银行全额低息贷款；国内外全程保姆式服务",
            "certification": "IHK/HWK职业资格证书",
            "allowance": "培训期间享津贴",
            "description": "德国双元制专业类别：医疗健康类。完成培训后可考取职业资格证书，与实习企业签订正式劳动合同。",
        },
        {
            "name": "德国机械制造类培训",
            "type": "双元制",
            "country": "德国",
            "recruitment_group": "18-35岁，高中及以上学历",
            "duration": "2-3.5年",
            "fees": "免学费",
            "features": "省属教育国企直接签协议；银行全额低息贷款；国内外全程保姆式服务",
            "certification": "IHK/HWK职业资格证书",
            "allowance": "培训期间享津贴",
            "description": "德国双元制专业类别：机械制造类。培训生每周三至四日在企业学习实践和手工技能。",
        },
        {
            "name": "德国酒店管理类培训",
            "type": "双元制",
            "country": "德国",
            "recruitment_group": "18-35岁，高中及以上学历",
            "duration": "2-3.5年",
            "fees": "免学费",
            "features": "省属教育国企直接签协议；银行全额低息贷款；国内外全程保姆式服务",
            "certification": "IHK/HWK职业资格证书",
            "allowance": "培训期间享津贴",
            "description": "德国双元制专业类别：酒店管理类。完成职业培训考取IHK/HWK职业资格证书后，可与企业签订正式劳动合同。",
        },
        # Singapore courses
        {
            "name": "新加坡2+2国际本科班",
            "type": "国际本科",
            "country": "新加坡",
            "recruitment_group": "应往届初中毕业生",
            "duration": "4年（国内2年+新加坡2年）",
            "fees": "四年学费总计约30-31万人民币",
            "features": "入学门槛低；授课评分机制灵活；就业前景广；学制短；留学费用低回报率高；学历含金量高",
            "certification": "世界综合排名200-500名左右大学颁发的毕业证书，学历回国受中国教育部认证",
            "allowance": "第三年新加坡公费0学费留学",
            "description": "前两年在国内培养基地学习新加坡国际课程，第三年前往新加坡公费0学费留学（酒店运营6个月理论+6个月带薪实习，航空运营9个月理论+6个月带薪实习），第四年直升本科毕业。",
        },
        {
            "name": "新加坡2+2+1本硕连读",
            "type": "本硕连读",
            "country": "新加坡",
            "recruitment_group": "应往届初中毕业生",
            "duration": "5年（2+2+1）",
            "fees": "详见各学年学费表",
            "features": "初中毕业经由2+2学制本科毕业后可直升硕士，最快1年制硕士毕业；可申请新加坡、中国香港、中国澳门、中国内地、英美澳加等TOP200名校硕士",
            "certification": "世界名校硕士毕业证书，学历回国受中国教育部认证",
            "allowance": "第三年新加坡公费0学费留学",
            "description": "初中毕业经由2+2学制本科毕业后，可直升硕士，最快1年制硕士毕业。为学生提供安全、快捷并有保证的升入世界名校的捷径。",
        },
        {
            "name": "新加坡0.5/1+2国际本科班",
            "type": "国际本科",
            "country": "新加坡",
            "recruitment_group": "高二在读、应往届高中毕业或中职中技同等学历毕业生",
            "duration": "2.5-3年（国内0.5/1年+新加坡2年）",
            "fees": "2.5/3年学费总计约25万-26万元人民币",
            "features": "入学门槛低；授课评分机制灵活；就业前景广；学制短；留学费用低回报率高",
            "certification": "世界综合排名200-500名左右大学颁发的毕业证书，学历回国受中国教育部认证",
            "allowance": "第二年新加坡公费0学费留学",
            "description": "第一年在国内参加0.5/1年预科课程，第二年前往新加坡公费0学费留学，第三年直升新加坡本科课程并毕业。",
        },
        {
            "name": "新加坡0.5/1+2+1本硕连读",
            "type": "本硕连读",
            "country": "新加坡",
            "recruitment_group": "高二在读、应往届高中毕业或中职中技同等学历毕业生",
            "duration": "3.5-4年（0.5/1+2+1）",
            "fees": "详见各学年学费表",
            "features": "高中毕业经由0.5/1+2学制本科毕业后可直升硕士，最快一年制硕士毕业；可申请TOP200名校硕士",
            "certification": "世界名校硕士毕业证书，学历回国受中国教育部认证",
            "allowance": "第二年新加坡公费0学费留学",
            "description": "高中毕业经由0.5/1+2学制本科毕业后可直升硕士，最快一年制硕士毕业。安全、快捷并有保证的升入世界名校的捷径。",
        },
        {
            "name": "新加坡6+6酒店运营大专就业班",
            "type": "大专就业",
            "country": "新加坡",
            "recruitment_group": "职高、中专、中职、技校，年龄满17岁",
            "duration": "1年（6个月理论+6个月带薪实习）",
            "fees": "详见学费表",
            "features": "无语言要求；节省大量时间；提升综合能力、英语水平、学历水平；解决就业问题",
            "certification": "大专文凭",
            "allowance": "实习薪资6000-8000元人民币/月",
            "description": "6个月理论知识学习提升学术能力，6个月带薪实习积累工作经验。实习结束100%推荐就业，就业薪资可达15000元人民币/月以上。",
        },
        {
            "name": "新加坡9+6航空运营大专就业班",
            "type": "大专就业",
            "country": "新加坡",
            "recruitment_group": "职高、中专、中职、技校，年满17周岁",
            "duration": "1年（9个月理论+6个月带薪实习）",
            "fees": "详见学费表",
            "features": "无语言要求；节省大量时间；提升综合能力、英语水平、学历水平；解决就业问题",
            "certification": "大专文凭",
            "allowance": "实习薪资6000-8000元人民币/月",
            "description": "9个月理论知识学习课程，6个月带薪实习课程。实习结束100%推荐就业，就业薪资可达15000元人民币/月以上。",
        },
        {
            "name": "一年制专升本/本升硕",
            "type": "学历提升",
            "country": "新加坡",
            "recruitment_group": "专科/本科毕业生",
            "duration": "专升本1-1.5年，本升硕1年",
            "fees": "详见具体项目",
            "features": "同等条件下，就读国外名校，专升本只需1.5年，本升硕仅需一年；实现弯道超车",
            "certification": "学历回国受中国教育部认证，享受留学生归国福利",
            "allowance": "-",
            "description": "国内专科升到本科需要2-3年，本科升到研究生也需要2-3年。同等条件下，就读国外名校，专升本只需1-1.5年，本科升硕士仅需一年。",
        },
        {
            "name": "新加坡一带一路工学交替项目",
            "type": "工学交替",
            "country": "新加坡",
            "recruitment_group": "职高、中专、中职、技校毕业生",
            "duration": "1年（6/9个月理论+6个月带薪实习）",
            "fees": "详见学费表",
            "features": "6个月理论知识学习提升学术能力，6个月带薪实习积累工作经验",
            "certification": "大专文凭",
            "allowance": "实习薪资6000-8000元人民币/月，就业薪资可达15000元人民币/月以上",
            "description": "6个月（9个月）理论知识学习课程让学生深入理解专业知识，6个月带薪实习课程中应用所学知识积累实际工作经验。只需一年即可获得大专文凭，实习结束100%推荐就业。",
        },
    ]
    for course_data in courses:
        existing = session.exec(select(Course).where(Course.name == course_data["name"])).first()
        if not existing:
            course = Course(**course_data)
            session.add(course)


def _seed_events(session: Session):
    """
    Source: knowledge/raw/公司信息/常见问答对.md (FAQ about events)
    Source: references/客户需求表.md (活动与讲座报名需求)
    """
    from datetime import datetime
    events = [
        {
            "name": "德国双元制项目说明会",
            "type": "项目说明会",
            "event_datetime": datetime(2026, 6, 15, 14, 0),
            "location": "广东省广州市越秀区东风东路723号高教大厦二楼",
            "description": "了解德国双元制教育模式、专业类别（医疗健康/机械制造/商贸会计/电子电器/汽车服务/酒店管理）、报名要求及办理流程。省属教育国企直接签协议，银行全额低息贷款。",
            "status": "active",
        },
        {
            "name": "新加坡国际本硕升学分享会",
            "type": "留学分享会",
            "event_datetime": datetime(2026, 6, 22, 10, 0),
            "location": "广东省广州市越秀区东风东路723号高教大厦二楼",
            "description": "介绍新加坡2+2国际本科班、0.5/1+2国际本科班、本硕连读等项目。四年学费总计约30-31万，学历回国受中国教育部认证。现场可参加入学笔试及面试。",
            "status": "active",
        },
        {
            "name": "海外留学招生官见面会",
            "type": "招生官见面会",
            "event_datetime": datetime(2026, 7, 10, 9, 0),
            "location": "广东省广州市越秀区东风东路723号高教大厦二楼",
            "description": "与德国及新加坡合作院校招生官面对面交流，了解院校申请门槛、签证要求及最新移民就业政策。现场完成活动预约与报名。",
            "status": "active",
        },
    ]
    for event_data in events:
        existing = session.exec(select(Event).where(Event.name == event_data["name"])).first()
        if not existing:
            event = Event(**event_data)
            session.add(event)


def _seed_users(session: Session):
    """
    Source: knowledge/raw/公司信息/公司新人指南.md (部门联系人信息)
    """
    users = [
        {"username": "admin", "password_hash": _hash_password("admin123"), "role": "admin"},
        {"username": "zhangmingyang", "password_hash": _hash_password("123456"), "role": "employee"},
        {"username": "chensiqi", "password_hash": _hash_password("123456"), "role": "employee"},
        {"username": "wangjianguo", "password_hash": _hash_password("123456"), "role": "employee"},
    ]
    for user_data in users:
        existing = session.exec(select(User).where(User.username == user_data["username"])).first()
        if not existing:
            user = User(**user_data)
            session.add(user)

    advisor = session.exec(select(User).where(User.username == "zhangmingyang")).first()
    if advisor:
        existing_student = session.exec(select(User).where(User.username == "student_demo")).first()
        if not existing_student:
            student = User(
                username="student_demo",
                password_hash=_hash_password("123456"),
                role="student",
                class_advisor_id=advisor.id,
            )
            session.add(student)


def seed_all():
    """Run all seed data functions. Idempotent - skips existing records."""
    with Session(engine) as session:
        _seed_organizations(session)
        _seed_courses(session)
        _seed_events(session)
        _seed_users(session)
        session.commit()
        print("[SEED] Default data initialized successfully.")
