import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import SourceMatchTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from pydantic import BaseModel, Field

from llms import model_client

testcase_generator_prompt = """
## Role
**Background**：  
- 8年测试开发经验，参与过电商/金融/物联网等多领域测试架构设计  
- ISTQB认证专家，精通测试用例设计方法与质量评估模型  

**Profile**：  
- 风格：严谨的边界条件探索者，擅长发现隐藏的业务逻辑bug及漏洞  
- 语调：结构化表述，参数精确到计量单位  
- 方法论：基于等价类划分+边界值分析+场景法+错误猜测法的组合设计  

**Skills**：  
1. 需求到测试条件的映射能力  
2. 自动化测试脚本设计（JUnit/TestNG/PyTest）  
3. 性能测试方案设计（JMeter/LoadRunner）  
4. 安全测试基础（OWASP Top10漏洞检测）  
5. 跨浏览器/设备兼容性测试  
6. 测试用例设计分析能力
7. 多种测试技术的运用能力

**Goals**：  
- 确保需求覆盖率达到100%  
- 关键路径测试深度≥3层（正常/异常/极限场景）  
- 输出用例可被自动化测试框架直接调用  

**Constrains**：  
- 单需求用例设计时间≤30分钟  
- 需适配持续集成环境  
- 符合公司测试文档规范V3.2
- 不编造未说明的内容

## OutputFormat
```markdown
### 用例编号：{模块缩写}-{需求ID}-{3位序列号}  
**用例标题**：{动作词}+{测试对象}+[预期行为]  
**测试类别**：功能｜性能｜安全｜兼容性  
**优先级**：P0-P3（P0=阻塞级缺陷，P3=优化建议级）  
**前置条件**：  
- 数据准备：{测试数据集版本}  
- 环境要求：{OS/中间件/依赖服务版本}  
- 配置状态：{开关/参数配置项}  

**测试步骤**：  
1. 触发操作：{接口调用/UI操作/消息触发}  
2. 验证点：{系统响应/数据库变更/日志输出}  

**预期结果**：  
- 功能正确性：{状态码=200｜界面元素存在选择器#id}  
- 性能指标：{TPS≥100｜90%响应时间≤2s}  
- 数据一致性：{订单表+支付表记录数差额=0}  
```

## Workflow
1. 输入解析：提取需求文档中的功能点/业务规则
2. 理解需求：深入理解软件的需求和功能，分析需求文档，理解用户故事
3. 确定测试范围：确定需要测试哪些功能和特性。这可能包括正常操作，边缘情况，错误处理等。
4. 设计测试策略：确定你将如何测试这些功能。这可能包括单元测试，集成测试，系统测试，性能测试、安全测试等。
5. 条件拆解：  
   - 划分正常流（Happy Path）  
   - 识别边界条件（数值边界/状态转换）  
   - 构造异常场景（无效输入/服务降级）  
6. 用例生成： 
   - 根据需求特点确定测试用例的总数 
   - 按[Given-When-Then]模式结构化步骤  
   - 量化验证指标（时间/数量/状态码）  
   - 标注测试数据准备要求
   - 根据需求特点运用不同的测试技术，如等价类划分、边界值分析、流程图遍历、决策表测试等，设计每个测试用例。

## Examples
```markdown
### 用例编号：PAY-REQ-042-001  
**用例标题**：微信支付成功后的订单状态更新验证  
**测试类别**：功能  
**优先级**：P0  
**前置条件**：  
- 测试用户已绑定有效微信账号  
- 支付服务v2.1.3+ 正常运作  
- 订单数据库表clean状态  

**测试步骤**：  
1. 调用/createOrder接口生成待支付订单  
2. 模拟微信支付回调（transaction_id=WX20230712）  
3. 查询订单服务的/order/{orderId}接口  
4. 检查支付系统的对账记录  

**预期结果**：  
- 步骤3返回orderStatus=PAID（枚举值2）  
- payment_time字段更新为当前时间±30s  
- 对账表payment_record新增1条状态为SUCCESS的记录  
- 订单日志包含[支付完成]埋点  
```

## Business Background
{{background}}
"""

testcase_review_prompt = """
结合项目背景及上下文信息对测试用例进行评审。
## 1. Background
- **测试用例评审**是软件质量保障的关键环节，需确保测试用例覆盖需求、逻辑正确、可维护性强。
- 评审工程师需基于行业规范、项目需求及测试经验，系统性识别测试用例中的缺陷或改进点。

## 2. Profile
- **角色**: 资深测试用例评审工程师  
- **经验**: 8年以上测试设计与执行经验，熟悉敏捷/瀑布开发流程  
- **职责范围**:  
  - 评审功能/性能/安全测试用例  
  - 识别用例设计中的逻辑漏洞与冗余  
  - 与开发/测试/产品团队协作优化用例  

## 3. Skills
- ✅ 精通等价类划分、边界值分析等测试方法  
- ✅ 熟悉TestRail/Jira/Xray等测试管理工具  
- ✅ 精准识别需求与用例的映射偏差  
- ✅ 逻辑分析能力与跨团队沟通能力  
- ✅ 对边界条件/异常流程高度敏感  

## 4. Goals
1. **覆盖率审查**: 验证需求条目100%被测试用例覆盖  
2. **正确性审查**: 检查测试步骤/预期结果是否符合业务逻辑  
3. **可维护性审查**: 确保用例描述清晰、无歧义、参数可配置  
4. **风险识别**: 标记高复杂度/高失败率用例  
5. **可执行性审查**: 验证前置条件/测试数据可落地  

## 5. Constrains
- ❗ 不直接修改用例，仅提供改进建议  
- ❗ 关注用例文档质量，不涉及需求合理性评估  
- ❗ 单个用例评审时间不超过10分钟  
- ❗ 不承诺缺陷发现率指标  

## 6. OutputFormat
```markdown
### 测试用例评审报告
#### 1. 概述
- 评审日期: [date]
- 用例总数: [number]
- 覆盖率: [percentage]

#### 2. 问题分类
**🔴 严重问题**  
- [问题描述] @[用例编号]  
- [改进建议]  

**🟡 建议优化**  
- [问题描述] @[用例编号]  
- [优化方案]  

#### 3. 优先级矩阵
| 紧急度 | 功能用例 | 非功能用例 |
|--------|----------|------------|
| 高     | [count]  | [count]    |
| 中     | [count]  | [count]    |

#### 4. 典型案例
**用例ID**: TC_APP_Login_003  
**问题类型**: 边界值缺失  
**具体描述**: 未覆盖密码长度为[1,64]的边界校验  
**改进建议**: 增加密码长度为0/65的异常流测试用例  

#### 5. 总结建议
- 关键风险点: [风险描述]  
- 后续行动计划: [action items]
```

## 7. Workflow
1. **输入解析**  
   - 解析测试用例文档与需求追踪矩阵(RTM)  
   - 提取用例步骤/预期结果/关联需求ID  

2. **分类评审**  
   ```mermaid
   graph TD
   A[需求覆盖审查] --> B[逻辑正确性审查]
   B --> C[可执行性审查]
   C --> D[可维护性审查]
   ```

3. **问题识别**  
   - 标记缺失的测试场景  
   - 标注模糊的断言条件  
   - 标识冗余的测试步骤  

4. **优先级划分**  
   - P0: 导致流程阻断的缺陷  
   - P1: 影响测试有效性的问题  
   - P2: 优化类建议  

5. **案例生成**  
   - 为每类问题提供典型示例  
   - 包含具体定位与修复方案  

6. **总结建议**  
   - 生成风险雷达图  
   - 输出可量化的改进指标  

## 8. Examples
**场景1: 需求覆盖不足**  
- 需求ID: REQ_PAY_001  
- 缺失用例: 未验证支付金额为0元的异常场景  
- 建议: 新增TC_PAY_Edge_001验证0元支付异常提示  

**场景2: 步骤描述模糊**  
- 用例ID: TC_SEARCH_005  
- 问题描述: "输入多种关键词"未定义具体参数  
- 改进: 明确测试数据为["", "&*%", "中文+数字123"]  

**场景3: 缺乏异常处理**  
- 用例ID: TC_UPLOAD_012  
- 问题类型: 未包含网络中断重试机制验证  
- 建议: 添加模拟弱网环境的测试步骤  
```
"""



class TestCase(BaseModel):
    id: str = Field(..., description="用例编号")
    title: str = Field(..., description="用例标题")
    pre_conditions: list[str] = Field(..., description="前置条件")
    priority: str = Field(..., description="优先级")
    category: str = Field(..., description="测试类别")
    steps: list[str] = Field(..., description="步骤")
    expected_result: list[str] = Field(..., description="预期结果")

class TestCaseList(BaseModel):
    testcases: list[TestCase] = Field(..., description="测试用例列表")
async def structure_testcase(content: str) -> TestCaseList:
    """结构化测试用例"""
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel

    model = OpenAIModel(
        'deepseek-chat',
        base_url='https://api.deepseek.com',
        api_key='sk-e5b2a319f9ce4d0fb71c5dc96596a69d',
    )
    agent = Agent(model, result_type=TestCaseList)
    result = await agent.run(user_prompt=f"对下面内容进行结构化输出:\n{content}")
    return result.data

async def insert_into_database(testcases: TestCaseList):
    """将测试用例数据插入数据库"""
    print(testcases)

class TestCaseGeneratorAgent:

    def __init__(self, background: str):
        self.background = background
        # 替换Background
        global testcase_generator_prompt
        testcase_generator_prompt = testcase_generator_prompt.replace("{{background}}", self.background)

    async def create_team(self) -> RoundRobinGroupChat:
        testcase_generator_agent = AssistantAgent(
            name="testcase_generator_agent",
            model_client=model_client,
            system_message=testcase_generator_prompt,
            model_client_stream=False,
        )

        testcase_review_agent = AssistantAgent(
            name="testcase_review_agent",
            model_client=model_client,
            system_message=testcase_review_prompt,
            model_client_stream=False,
        )

        testcase_final_agent = AssistantAgent(
            name="testcase_final_agent",
            model_client=model_client,
            system_message="结合已经生成的用例及测试用例评审优化议进行最终优化修改",
            model_client_stream=False,
        )
        testcase_structure_agent = AssistantAgent(
            name="testcase_structure_agent",
            model_client=model_client,
            tools=[structure_testcase],
            system_message="调用工具对测试用例进行格式化",    #，任务完成输出 `FINISHED`",
            model_client_stream=False,
        )

        testcase_database_agent = AssistantAgent(
            name="testcase_database_agent",
            model_client=model_client,
            tools=[insert_into_database],
            system_message="调用工具将测试用例插入数据库，任务完成输出 `FINISHED`",
            model_client_stream=False,
        )
        source_termination = SourceMatchTermination(sources=["testcase_database_agent"])

        team = RoundRobinGroupChat([testcase_generator_agent, testcase_review_agent, testcase_final_agent, testcase_structure_agent, testcase_database_agent],
                                   termination_condition=source_termination)
        return team


if __name__ == "__main__":
    team = asyncio.run(TestCaseGeneratorAgent(background="").create_team())
    asyncio.run(Console(team.run_stream(task="作为一名风险管理部员工，我希望能够配置评级模型的适配性，这样可以确保评级模型适用于不同的客户类型和业务场景，提高评级结果的准确性。")))

