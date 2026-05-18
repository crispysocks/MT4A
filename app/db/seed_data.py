"""
Database seed data initialization.
All default data is sourced from knowledge/raw/ documents.
"""
import bcrypt
from datetime import datetime
from sqlmodel import Session, select
from app.db.connection import engine
from app.db.models import (
    Course, DailyReport, Event, Organization, User,
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


def _seed_daily_reports(session: Session):
    """Seed sample daily reports for employee users."""
    users_map = {}
    for username in ["zhangmingyang", "chensiqi", "wangjianguo"]:
        user = session.exec(select(User).where(User.username == username)).first()
        if user:
            users_map[username] = user.id

    reports = [
        {
            "user_id": users_map.get("zhangmingyang"),
            "department": "双元制事业部",
            "content": "今天接待了5组咨询德国双元制项目的家长和学生，其中2组当场签署了意向协议。重点介绍了机电一体化和医疗健康两个专业方向，家长对免学费和企业发放酬金的模式认可度很高。下午整理了本周的客户跟进表，发现有三组客户处于犹豫阶段，计划明天逐一电话回访，针对他们的顾虑——主要是语言关和生活适应问题——准备一份Q&A文档。",
            "summary": "接待5组咨询，签署2份意向协议；明天计划对3组犹豫客户电话回访。",
            "submitted_at": datetime(2026, 5, 15, 17, 30),
        },
        {
            "user_id": users_map.get("zhangmingyang"),
            "department": "双元制事业部",
            "content": "上午参加了双元制项目课程升级讨论会，学院方面提出新增「可再生能源技术」方向。收集了目前德国合作院校的可再生能源专业设置和就业数据，整理了一份对比分析表。下午跟进上周签约的李同学的材料审核进度，德方已确认接收，下一步需要办理签证预约。另外给新入职的实习生做了双元制项目知识培训。",
            "summary": "参加课程升级讨论，提议新增可再生能源方向；李同学材料已通过德方审核。",
            "submitted_at": datetime(2026, 5, 16, 18, 0),
        },
        {
            "user_id": users_map.get("zhangmingyang"),
            "department": "双元制事业部",
            "content": "今日外勤——前往深圳某职业高中开展德国双元制宣讲，到场学生约120人。宣讲效果不错，现场回收有效咨询表36份，其中机电一体化15份、酒店管理12份、医疗健康9份。与该校就业办达成初步合作意向，后续将安排专场说明会。回到办公室已六点半，整理了意向学生信息并录入CRM系统。",
            "summary": "深圳职高宣讲120人，回收36份有效咨询表；与该校达成合作意向。",
            "submitted_at": datetime(2026, 5, 17, 19, 0),
        },
        {
            "user_id": users_map.get("chensiqi"),
            "department": "课后服务事业部",
            "content": "今天处理了3起家长投诉。第一起反映孩子课后作业辅导老师频繁更换，已协调安排固定老师对接；第二起关于课程费用退费问题，已向财务提交退款申请并告知家长3-5个工作日到账；第三起是老师上课迟到问题，已约谈相关老师并提出警告。同时完成了本月满意度调查问卷的设计，明天开始发放。",
            "summary": "处理3起投诉（师资更换、退费、迟到），完成满意度问卷设计。",
            "submitted_at": datetime(2026, 5, 15, 17, 45),
        },
        {
            "user_id": users_map.get("chensiqi"),
            "department": "课后服务事业部",
            "content": "上午走访了合作的3家社区课后服务中心，检查课程质量和安全设施。其中一家发现消防通道堆放杂物，已要求立即整改并拍照留档。下午和教研团队讨论了暑期特色课程方案，初步确定开设「小小工程师」「少儿编程启蒙」和「非遗手工」三个主题。与市场部同步了暑期招生的宣传素材需求。",
            "summary": "走访3家社区服务中心，发现1处安全隐患已整改；确定暑期3个特色课程主题。",
            "submitted_at": datetime(2026, 5, 16, 17, 30),
        },
        {
            "user_id": users_map.get("chensiqi"),
            "department": "课后服务事业部",
            "content": "今天完成满意度调查的线上发放工作，通过班级群和公众号推送，目前回收有效问卷158份。初步数据显示整体满意度88.6%，较上期提升2.3个百分点。不足之处主要集中在「课程多样性」和「课后反馈及时性」两项。已和产品团队沟通，计划引入每周学习报告自动推送功能。",
            "summary": "满意度调查回收158份，整体满意率88.6%；计划引入每周学习报告推送。",
            "submitted_at": datetime(2026, 5, 17, 18, 15),
        },
        {
            "user_id": users_map.get("wangjianguo"),
            "department": "智能装备事业部",
            "content": "今天完成了智慧校园项目中AI考勤系统的联调测试。人脸识别准确率达到99.2%，但在逆光场景下下降到96.5%，已反馈算法团队优化。下午与某区教育局信息中心开视频会，演示了智慧校园一期功能模块，对方对食堂消费系统和宿舍管理系统比较感兴趣，约了下周现场演示。",
            "summary": "AI考勤系统联调完成，正光99.2%准确率；区教育局对食堂和宿舍系统感兴趣。",
            "submitted_at": datetime(2026, 5, 15, 18, 0),
        },
        {
            "user_id": users_map.get("wangjianguo"),
            "department": "智能装备事业部",
            "content": "上午去合作学校现场部署智慧班牌设备，一共安装了12个教室的门禁和电子班牌终端。遇到一处在装修阶段的教室布线问题，与施工方沟通后确定了走线方案，预计下周一完成安装。下午整理设备部署手册并更新到项目文档库。另收到3家学校关于智慧食堂的咨询，已转交销售团队跟进。",
            "summary": "完成12间教室智慧班牌安装；3家校咨询智慧食堂，已转销售。",
            "submitted_at": datetime(2026, 5, 16, 17, 0),
        },
        {
            "user_id": users_map.get("wangjianguo"),
            "department": "智能装备事业部",
            "content": "今天重点是新能源充电桩项目的需求评审。与甲方确认了园区充电桩布局方案，总计36个快充桩+12个慢充桩。技术层面讨论了与现有配电系统的兼容性，以及后期运维管理平台的数据对接方案。会后整理了会议纪要和项目排期，预计6月初开始施工。另外处理了2个线上运维工单。",
            "summary": "新能源充电桩需求评审通过，36快充+12慢充；整理项目排期，6月初施工。",
            "submitted_at": datetime(2026, 5, 17, 18, 30),
        },
    ]

    for r in reports:
        if r["user_id"] is None:
            continue
        existing = session.exec(
            select(DailyReport).where(
                DailyReport.user_id == r["user_id"],
                DailyReport.content == r["content"],
            )
        ).first()
        if not existing:
            report = DailyReport(**r)
            session.add(report)


def seed_all():
    """Run all seed data functions. Idempotent - skips existing records."""
    with Session(engine) as session:
        _seed_organizations(session)
        _seed_courses(session)
        _seed_events(session)
        _seed_users(session)
        _seed_daily_reports(session)
        session.commit()
        print("[SEED] Default data initialized successfully.")
