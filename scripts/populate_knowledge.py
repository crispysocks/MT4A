"""知识库填充脚本 - 将文档嵌入向量数据库"""

from app.rag.store import ChromaStore


def populate():
    store = ChromaStore()

    documents = [
        # company/public - 公开信息，全员可见
        {
            "text": "公司成立于2010年，专注于教育信息化领域，总部位于北京。",
            "id": "pub_001",
            "metadata": {"source": "company/public", "type": "about"}
        },
        {
            "text": "公司使命：用技术赋能教育创新，让每个人都能获得优质教育资源。",
            "id": "pub_002",
            "metadata": {"source": "company/public", "type": "mission"}
        },
        {
            "text": "公司地址：北京市海淀区中关村大街1号院1号楼。联系电话：010-12345678。",
            "id": "pub_003",
            "metadata": {"source": "company/public", "type": "contact"}
        },
        {
            "text": "主要业务：留学咨询、语言培训、教育科技产品开发。",
            "id": "pub_004",
            "metadata": {"source": "company/public", "type": "business_scope"}
        },

        # company/internal - 内部信息，仅员工可见
        {
            "text": "员工出差报销标准：国内机票经济舱，实报实销，单次上限5000元，需提供发票。",
            "id": "int_001",
            "metadata": {"source": "company/internal", "type": "policy"}
        },
        {
            "text": "考勤规定：上班时间9:00，下班时间18:00，午休12:00-13:00。迟到超过3次扣当月绩效。",
            "id": "int_002",
            "metadata": {"source": "company/internal", "type": "policy"}
        },
        {
            "text": "请假制度：年假需提前3天申请，病假需提供医院证明，事假扣当日工资。",
            "id": "int_003",
            "metadata": {"source": "company/internal", "type": "policy"}
        },
        {
            "text": "薪资发放：每月10日发放上上月工资，转账至绑定银行卡，支持分期付款的学员另有规定。",
            "id": "int_004",
            "metadata": {"source": "company/internal", "type": "policy"}
        },

        # business - 业务信息，学生/员工/访客均可见
        {
            "text": "留学申请流程：1.初步咨询 2.签约付费 3.选校方案 4.材料准备 5.提交申请 6.面试辅导 7.录取通知 8.行前准备。",
            "id": "biz_001",
            "metadata": {"source": "business", "type": "process"}
        },
        {
            "text": "语言培训课程：新托福基础班（80课时）、强化班（40课时）、雅思直通班（60课时）、SAT突破班（50课时）。",
            "id": "biz_002",
            "metadata": {"source": "business", "type": "course"}
        },
        {
            "text": "收费标准：咨询费单项3000元，全程服务20000元，含选校、文书、申请、签证全流程。",
            "id": "biz_003",
            "metadata": {"source": "business", "type": "pricing"}
        },
        {
            "text": "成功案例：累计服务学员超过5000人，美国Top30录取率35%，英国G5录取率28%。",
            "id": "biz_004",
            "metadata": {"source": "business", "type": "achievement"}
        },

        # policy - 政策信息，学生/员工/访客均可见
        {
            "text": "研究生项目申请截止日期：每年3月31日（秋季入学），10月31日（春季入学）。",
            "id": "pol_001",
            "metadata": {"source": "policy", "type": "deadline"}
        },
        {
            "text": "申请材料清单：本科成绩单（中英文）、两封推荐信、个人陈述（PS）、护照复印件、资产证明。",
            "id": "pol_002",
            "metadata": {"source": "policy", "type": "requirements"}
        },
        {
            "text": "语言成绩要求：托福80分以上或雅思6.5分以上，部分专业需要GRE/GMAT成绩。",
            "id": "pol_003",
            "metadata": {"source": "policy", "type": "requirements"}
        },
        {
            "text": "退款政策：签约后7天内可全额退款，超过7天按服务进度扣除已发生费用后退还余额。",
            "id": "pol_004",
            "metadata": {"source": "policy", "type": "refund"}
        },
    ]

    texts = [d["text"] for d in documents]
    ids = [d["id"] for d in documents]
    metadatas = [d["metadata"] for d in documents]

    store.add_documents(texts, ids, metadatas)
    print(f"已填充 {len(texts)} 条知识")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)
    populate()