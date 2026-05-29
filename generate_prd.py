#!/usr/bin/env python3
"""
Generate PRD V2.2 Word document for 跨部门OpenCLAW协作系统
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

OUTPUT_PATH = "E:/project/openclaw-platform/PRD-V2.2-跨部门OpenCLAW协作系统.docx"

doc = Document()

# ============================================================
# Global styles setup
# ============================================================
style = doc.styles['Normal']
font = style.font
font.name = 'SimSun'  # 宋体
font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
pf = style.paragraph_format
pf.line_spacing = 1.5
pf.space_before = Pt(0)
pf.space_after = Pt(6)

# Page margins
for section in doc.sections:
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

# ============================================================
# Helpers
# ============================================================
def set_run_font(run, name='微软雅黑', size=Pt(10.5), bold=False, color=None, east_asia='微软雅黑'):
    run.font.name = name
    run.font.size = size
    run.bold = bold
    if color:
        run.font.color.rgb = color
    r = run._element
    rPr = r.find(qn('w:rPr'))
    if rPr is None:
        rPr = parse_xml(f'<w:rPr {nsdecls("w")}></w:rPr>')
        r.insert(0, rPr)
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}></w:rFonts>')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), east_asia)

def add_heading_styled(text, level=1):
    """Add heading with custom style"""
    p = doc.add_paragraph()
    run = p.add_run(text)
    if level == 1:
        set_run_font(run, size=Pt(16), bold=True)
        pf = p.paragraph_format
        pf.space_before = Pt(12)
        pf.space_after = Pt(8)
    elif level == 2:
        set_run_font(run, size=Pt(14), bold=True)
        pf = p.paragraph_format
        pf.space_before = Pt(10)
        pf.space_after = Pt(6)
    elif level == 3:
        set_run_font(run, size=Pt(12), bold=True)
        pf = p.paragraph_format
        pf.space_before = Pt(8)
        pf.space_after = Pt(4)
    elif level == 4:
        set_run_font(run, size=Pt(11), bold=True)
        pf = p.paragraph_format
        pf.space_before = Pt(6)
        pf.space_after = Pt(3)
    return p

def add_body_text(text, bold=False, indent=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, name='宋体', east_asia='宋体', size=Pt(10.5), bold=bold)
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    return p

def set_cell_shading(cell, color):
    """Set cell background color"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}" w:val="clear"/>')
    tcPr.append(shading)

def set_cell_text(cell, text, bold=False, color=None, size=Pt(9), font_name='宋体'):
    """Set cell text with formatting, clearing existing paragraphs"""
    for p in cell.paragraphs:
        for r in p.runs:
            r.clear()
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run_font(run, name=font_name, east_asia=font_name, size=size, bold=bold, color=color)

def add_table(headers, rows, col_widths=None):
    """Add a styled table with blue header and alternating rows"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    # Header row - dark blue background, white bold text
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_shading(cell, '2B579A')
        set_cell_text(cell, header, bold=True, color=RGBColor(255, 255, 255), size=Pt(9), font_name='微软雅黑')

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_text in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            if r_idx % 2 == 1:
                set_cell_shading(cell, 'EDF4FC')
            set_cell_text(cell, str(cell_text), size=Pt(9), font_name='宋体')

    # Set column widths if provided
    if col_widths:
        for row in table.rows:
            for i, width in enumerate(col_widths):
                if i < len(row.cells):
                    row.cells[i].width = width

    doc.add_paragraph()  # spacing after table
    return table

def add_page_break():
    doc.add_page_break()

# ============================================================
# PAGE 1: COVER
# ============================================================
# Add empty paragraphs for spacing
for _ in range(6):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('跨部门 OpenCLAW 协作系统')
set_run_font(run, name='微软雅黑', east_asia='微软雅黑', size=Pt(26), bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('产品需求文档（PRD）')
set_run_font(run, name='微软雅黑', east_asia='微软雅黑', size=Pt(18), bold=False)

doc.add_paragraph()

# Version info table on cover
info_items = [
    ('版本', 'V2.2 · PM 终审版'),
    ('日期', '2026-05-25'),
    ('状态', '待审批'),
    ('产品经理', '老高（PM）'),
]

table = doc.add_table(rows=len(info_items), cols=2)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (k, v) in enumerate(info_items):
    cell_k = table.rows[i].cells[0]
    cell_v = table.rows[i].cells[1]
    set_cell_shading(cell_k, '2B579A')
    set_cell_text(cell_k, k, bold=True, color=RGBColor(255, 255, 255), size=Pt(11), font_name='微软雅黑')
    set_cell_text(cell_v, v, size=Pt(11), font_name='微软雅黑')

doc.add_paragraph()
# Separator line
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('—' * 40)
set_run_font(run, color=RGBColor(0x99, 0x99, 0x99))

doc.add_paragraph()

# Role list
role_items = [
    '项目客户：高总', '架构师：Architect', '后端：Backend',
    '前端：Frontend', '测试：Tester', '评审：Reviewer', '运维：Deploy'
]
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('  |  '.join(role_items))
set_run_font(run, name='微软雅黑', east_asia='微软雅黑', size=Pt(11))

add_page_break()

# ============================================================
# PAGE 2: 版本修订记录
# ============================================================
add_heading_styled('版本修订记录', level=1)

revision_headers = ['版本', '日期', '变更内容']
revision_rows = [
    ['V1.0', '2026-05-25', '初稿'],
    ['V2.0', '2026-05-25', '全员第一轮 46 条意见整合'],
    ['V2.1', '2026-05-25', '全员第二轮 46 条意见全部整合'],
    ['V2.2', '2026-05-25', '全员第三轮 8 条意见全部整合：\nReviewer 3条 + Backend 4条 + PM 1条'],
]
add_table(revision_headers, revision_rows)

add_body_text('V2.2 具体修订内容：', bold=True)
v22_details = [
    '47. Reviewer — NATS JWT 认证 + Nginx 透传（决策1）',
    '48. Reviewer — progress_seq 字段补到 tasks 表（§9.1）',
    '49. Reviewer — 站内消息 MVP 存储方案说明（§10.6）',
    '50. Backend — 状态机补自动兜底分配虚线路径（§6.1）',
    '51. Backend — 离线丢弃结果加系统通知 + 日志（§7.1）',
    '52. Backend — fallback 链收紧至 15s/30s（§6.3）',
    '53. Backend — 模型下载带宽控制加 Redis 分布式锁（§6.2）',
    '54. PM（自查） — Nginx WS proxy_read_timeout + worker_connections 补配置示例（决策1）',
]
for detail in v22_details:
    p = doc.add_paragraph()
    run = p.add_run('• ' + detail)
    set_run_font(run, name='宋体', east_asia='宋体', size=Pt(10))

add_page_break()

# ============================================================
# PAGE 3: 目录
# ============================================================
add_heading_styled('目录', level=1)

toc_items = [
    '一、产品概述',
    '二、关键决策',
    '三、功能模块总览',
    '四、UI 原型设计',
    '    4.1 任务列表页',
    '    4.2 任务详情/领取页',
    '    4.3 部门共享库',
    '    4.4 管理后台',
    '    4.5 个人设置',
    '    4.6 站内消息中心',
    '五、交互逻辑',
    '六、API 接口定义',
    '七、数据库设计',
    '八、技术架构',
    '九、错误场景',
    '十、成本测算',
]
for item in toc_items:
    p = doc.add_paragraph()
    run = p.add_run(item)
    if not item.startswith('    '):
        set_run_font(run, name='微软雅黑', east_asia='微软雅黑', size=Pt(12), bold=True)
    else:
        set_run_font(run, name='宋体', east_asia='宋体', size=Pt(10.5))

add_page_break()

# ============================================================
# 一、产品概述
# ============================================================
add_heading_styled('一、产品概述', level=1)

add_heading_styled('1.1 背景', level=2)
add_body_text(
    '中小型企业多部门使用 OpenCLAW 进行 AI 任务处理，但存在以下痛点：',
    indent=True
)
pain_points = [
    '各部门各自部署 OpenCLAW，模型重复采购，GPU 资源浪费',
    '跨部门协作没有统一平台，任务流转靠口头/群聊，不可追踪',
    '高价值大参数模型不是所有部门都买得起/跑得动',
    '缺乏统一的任务进度管理和成果共享机制',
]
for pt in pain_points:
    p = doc.add_paragraph()
    run = p.add_run('• ' + pt)
    set_run_font(run, name='宋体', east_asia='宋体')

add_heading_styled('1.2 目标', level=2)
add_body_text(
    '构建轻量级、低成本、可插拔的跨部门 OpenCLAW 协作平台，实现：',
    indent=True
)
goals = [
    '主-分节点统一调度：任务下发 → 执行 → 回传全流程闭环',
    '模型统一管理，按部门按任务类型自动路由最优性价比模型',
    '任务进度实时可见，成果一键共享',
    '首月降本 30%（模型调用共享池化，结果缓存降低重复计算）',
]
for g in goals:
    p = doc.add_paragraph()
    run = p.add_run(f'{goals.index(g)+1}. {g}')
    set_run_font(run, name='宋体', east_asia='宋体')

add_heading_styled('1.3 目标用户', level=2)
user_headers = ['角色', '典型用户', '核心需求']
user_rows = [
    ['系统管理员', 'IT主管', '节点管理、模型配置、数据看板、配额设置'],
    ['部门主管', '研发/市场/人事负责人', '分配任务、看部门工单、看成本统计、锁定模型范围'],
    ['普通员工', '研发工程师/文案/HR', '领取任务、执行、提交成果、查看共享库'],
]
add_table(user_headers, user_rows)

add_page_break()

# ============================================================
# 二、关键决策
# ============================================================
add_heading_styled('二、关键决策', level=1)

# Decision 1
add_heading_styled('决策 1：连接方案 → NATS + JetStream', level=2)
add_body_text('最终结论：NATS JetStream（全员一致通过）', bold=True)

nats_headers = ['维度', 'NATS', 'RabbitMQ', 'Redis Streams']
nats_rows = [
    ['二进制大小', '~20MB', '~150MB + Erlang VM', '依赖 Redis（~30MB）'],
    ['内存占用', '空闲 ~5MB', '空闲 ~50MB+', '取决于用途'],
    ['部署复杂度', '单文件启动', '需配 Erlang 环境', '需额外装 Redis'],
    ['持久化', '✅ JetStream', '✅ 完善', '✅ RDB/AOF'],
    ['ACK 机制', '✅ at-least-once', '✅ 完善', '✅ 需手写'],
    ['前端 WS 原生支持', '✅ 原生', '❌ 需额外网关', '❌ 需自己封装'],
    ['运维成本', '低', '高', '中'],
]
add_table(nats_headers, nats_rows)

add_body_text('强制配置（Reviewer + Deploy 要求）：', bold=True)
add_body_text('1. NATS WS 端口不暴露公网，前端和 NATS 之间加 Nginx 反向代理层')
add_body_text('2. NATS JWT/Nkeys 认证：所有 Agent 连接时需携带凭证，NATS 原生 Account/User 的 subs/pub 权限声明限制每个 Agent 只能订阅/发布本部门 topic')
add_body_text('3. 前端通过 wss://面板域名/ws/nats 连接到 Nginx，Nginx 做 TLS 终止 + 身份透传，NATS 层面做 topic 权限校验，Nginx 不负责判断 topic 归属')
add_body_text('4. 必须开 JetStream，at-least-once + 手动 ACK')
add_body_text('5. JetStream 配置：max_msg_size=10MB、max_msgs_per_stream=100000、max_bytes_per_stream=1GB')

add_body_text('Nginx WS 代理配置：', bold=True)
nginx_config = '''location /ws/nats/ {
    proxy_pass http://127.0.0.1:9222/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}
worker_connections 1024;'''
p = doc.add_paragraph()
run = p.add_run(nginx_config)
set_run_font(run, name='Consolas', size=Pt(8.5))

# Decision 2
add_heading_styled('决策 2：服务器规格 → 4C8G 轻量云起步', level=2)
add_body_text('MVP 阶段用 2C4G 当心 MQ + Web 面板 + 数据库三者同时跑时撑不住。起步用 4C8G（阿里云/腾讯云轻量云约 ¥200-300/月），后续上 Docker Compose 编排，扩缩容一条命令搞定。')

# Decision 3
add_heading_styled('决策 3：任务分配 → 手动领取为主 + 自动兜底', level=2)
add_body_text('MVP 手动领取，但必须做以下机制：')
add_body_text('1. 手动领取（MVP 核心）：员工在 Web 面板上看到待领取任务列表，主动点击领取')
add_body_text('2. 30 分钟超时自动释放：员工领取后超过 30 分钟不点「开始处理」，任务自动回到待领取池，并记录异常日志')
add_body_text('3. 自动兜底分配：assignment_strategy = "manual" 的任务永远不触发自动兜底；"auto" 或 "hybrid" 的任务，10 分钟无人领取时触发自动兜底')
add_body_text('4. 分布式锁：手动领取和自动兜底共享同一把 Redis 分布式锁（Key = task:lock:{task_id}，TTL = 10 秒）')
add_body_text('5. 数据库字段预留：任务表增加 assignment_strategy 字段（manual / auto / hybrid）')

# Decision 4
add_heading_styled('决策 4：模型路由 → 三级模型选择机制', level=2)
add_body_text('第一级（默认自动）：主节点自动路由，默认走最便宜的模型')
add_body_text('  模型路由表按「任务类型 + 部门」自动匹配，例如：文档摘要 → qwen2.5-7b（本地，¥0），代码审查 → deepseek-coder-7b（本地，¥0）')
add_body_text('第二级（员工可选覆盖）：提交/领取任务时可选「换模型」')
add_body_text('  下拉框显示可用模型清单，旁边显示成本对比，选了贵的弹窗确认「成本警告」，但不强制拦截')
add_body_text('第三级（管理员锁）：部门主管可锁定某些任务的模型范围')
add_body_text('  锁定后新任务默认走锁定模型，已分配但未执行的任务保持原选择不强制重置。配置变更通过 NATS 推送热生效')

add_page_break()

# ============================================================
# 三、功能模块总览
# ============================================================
add_heading_styled('三、功能模块总览', level=1)

module_headers = ['功能模块', '功能项', '描述', 'MVP', '来源']

module_rows = [
    ['任务管理', '创建任务', '管理员/主管/员工创建，选目标部门、模型、优先级', '✅', 'PM'],
    ['任务管理', '任务分配', '自动按空闲度推荐 / 手动指定', '✅', 'PM'],
    ['任务管理', '任务领取', '员工在 Web 面板看到待领取任务，一键接单', '✅', 'PM'],
    ['任务管理', '领取超时释放', '领取后 30 分钟未开始，自动释放回池', '✅', 'Reviewer+Tester'],
    ['任务管理', '自动兜底分配', 'auto/hybrid 任务 10 分钟无人领 → 自动派给负载最低节点', '✅', 'Architect'],
    ['任务管理', '任务执行', '员工本地 Agent 自动执行，进度上报 NATS Pub/Sub', '✅', 'PM'],
    ['任务管理', '任务重试', '失败自动重试（可配次数），超过进死信队列', '✅', 'Tester'],
    ['任务管理', '成果提交', 'Agent 自动上传（MD5 校验）→ 主管审核 → 归档', '✅', 'PM'],
    ['任务管理', '任务自动回收', '领取后超 2 小时无活动，自动回收通知管理员', '✅', 'Tester'],
    ['员工分节点 Agent', '连接主节点', '启动时 NATS 注册，JWT 验证部门+身份', '✅', 'PM'],
    ['员工分节点 Agent', '心跳上报', '每 30 秒上报存活 + 并发数 + 资源占用（→ Redis）', '✅', 'PM'],
    ['员工分节点 Agent', '模型可用性上报', '启动时上报本地模型清单 + 显存/内存使用率', '✅', 'PM'],
    ['员工分节点 Agent', '拉取任务', '主动从 NATS 队列拉取分配给自己的任务', '✅', 'PM'],
    ['员工分节点 Agent', '资源下载', '从 MinIO 下载 prompt 模板、参考文档等', '✅', 'PM'],
    ['员工分节点 Agent', '任务本地缓存', 'Agent 拉到任务后存本地 SQLite，断网也能继续执行', '✅', 'PM'],
    ['员工分节点 Agent', '进度上报', 'NATS Pub/Sub 到 task.progress.{task_id}，前端 WS 实时接收', '✅', 'PM'],
    ['员工分节点 Agent', '成果回传', '执行完成上传 MinIO（含 MD5 校验），返回 result_url', '✅', 'PM'],
    ['员工分节点 Agent', '断网重连', '指数退避重连（1s→2s→4s→8s→16s），恢复后批量回传', '✅', 'PM'],
    ['员工分节点 Agent', '自动更新', '启动时检查版本，后台静默下载，下次重启时替换', '✅', 'Reviewer+Deploy'],
    ['员工分节点 Agent', '模型下载带宽控制', 'Redis 分布式锁保证同一时间只有 1 个 Agent 拉取', '✅', 'Backend'],
    ['模型路由与管理', '模型注册表', '按任务类型匹配推荐模型 + 备用模型', '✅', 'PM'],
    ['模型路由与管理', '三级选择', '自动路由 → 员工可选覆盖 → 管理员锁', '✅', 'PM'],
    ['模型路由与管理', 'fallback 链', '15s→15s→30s→30s 总最坏窗口 90s 以内', '✅', 'Backend'],
    ['模型路由与管理', '配额管理', '双层配额：计算配额 + 费用配额', '✅', 'Architect+Tester'],
    ['模型路由与管理', '管理员锁热更新', 'NATS 推送热生效，已分配任务不强制重置', '✅', 'Architect'],
    ['成果共享', '一键分享', '员工完成→点击「分享」→选同事/部门（同部门自动归档）', '✅', 'PM'],
    ['成果共享', '跨部门分享', '选对方部门 → 通知对方主管 → 审批后入库', '✅', 'PM'],
    ['成果共享', '部门共享库', '自动归档到部门共享 MinIO 目录', '✅', 'PM'],
    ['成果共享', '文件上传约束', '单文件上限 50MB，SHA256 校验，文件类型白名单', '✅', 'Backend+Deploy'],
    ['监控与运维', '任务看板', '各部门待处理/处理中/完成数', '✅', 'PM'],
    ['监控与运维', 'Agent 状态', '在线/离线/suspected_failure Agent 列表', '✅', 'PM'],
    ['监控与运维', '成本统计', '各部门每日/每周模型调用费用', '✅', 'PM'],
    ['监控与运维', '灰度上线', '先人事部全量试用，观察失败率和延迟', '✅', 'PM'],
    ['监控与运维', 'Prometheus 指标', '任务排队数、完成数、失败率、平均耗时', '✅', 'PM'],
    ['监控与运维', '告警规则', 'NATS 队列深度 > 50、心跳丢失 > 120s、磁盘 > 85%、失败率 > 5%', '✅', 'Deploy'],
    ['监控与运维', '日志采集', '各服务写本地日志文件（JSON 格式，按天轮转）+ audit_logs 表', '✅', 'Architect'],
    ['通知机制', '浏览器 Notification', '仅当浏览器打开时生效', '✅', 'PM'],
    ['通知机制', '浏览器标题闪动', '有新任务时标签页标题闪烁', '✅', 'PM'],
    ['通知机制', '站内消息中心', 'Web 面板右上角铃铛图标，NATS WS 实时推送', '✅', 'PM'],
    ['通知机制', '邮件通知', '任务分配、超时回收时发送', 'V2', 'PM'],
]
add_table(module_headers, module_rows)

add_page_break()

# ============================================================
# 四、UI 原型设计
# ============================================================
add_heading_styled('四、UI 原型设计', level=1)
add_body_text('注：以下页面原型使用表格+文字描述，不包含图片。原型设计文件参考路径：')
add_body_text('• E:/project/openclaw-platform/01-task-list.excalidraw — 任务列表页原型')
add_body_text('• E:/project/openclaw-platform/02-task-detail.excalidraw — 任务详情页原型')
add_body_text('• E:/project/openclaw-platform/03-shared-library.excalidraw — 共享库原型')
add_body_text('• E:/project/openclaw-platform/04-admin-panel.excalidraw — 管理后台原型')
add_body_text('• E:/project/openclaw-platform/05-user-settings.excalidraw — 个人设置原型')
add_body_text('• E:/project/openclaw-platform/06-notifications.excalidraw — 消息中心原型')
add_body_text('• E:/project/openclaw-platform/07-interaction-flow.excalidraw — 交互流程图')

# 4.1
add_heading_styled('4.1 任务列表页', level=2)
add_body_text('页面概述：员工登录后默认首页，以卡片形式展示待领取/处理中/已完成的任务。', bold=True)

layout_headers = ['区域', '元素', '说明']
layout_rows_41 = [
    ['顶部导航栏', 'Logo + 导航链接(我的任务/共享库/管理后台)', '导航切换页面'],
    ['顶部导航栏', '铃铛图标(未读小红点) + 用户头像', '消息中心和用户菜单入口'],
    ['Tab 栏', '待领取 / 处理中 / 已完成', '点击切换，默认显示「待领取」'],
    ['Tab 栏', 'Tab 数量角标', '每个 Tab 显示当前状态的任务数量'],
    ['任务卡片', '优先级色标(红/黄/灰)', '红色=紧急，黄色=普通，灰色=低优先级'],
    ['任务卡片', '任务标题 + 部门名', '显示任务名称和所属部门'],
    ['任务卡片', '创建时间 + 推荐模型', '任务创建时间和系统推荐模型名称'],
    ['任务卡片', '积分 + 领取按钮', '任务积分值和蓝色领取按钮'],
    ['加载更多', '分页器或滚动加载', '支持分页浏览更多任务'],
]
add_table(layout_headers, layout_rows_41)

# 4.2
add_heading_styled('4.2 任务详情/领取页', level=2)
add_body_text('页面概述：点击任务卡片后进入的详情页面，展示完整任务信息和模型选择。', bold=True)

layout_rows_42 = [
    ['顶部', '返回按钮 + 任务标题', '返回任务列表，显示当前任务名称'],
    ['任务信息区', '部门 / 创建人 / 截止时间 / 描述', '展示任务的完整信息'],
    ['模型选择区', '3 个模型卡片（含成本对比）', '推荐模型、备用模型、高级模型，显示每次调用费用对比'],
    ['模型选择区', '管理员锁定标识', '管理员锁定时 disabled + tooltip：「该模型由管理员锁定」'],
    ['模型选择区', '本地安装状态标识', '本地未安装时灰色显示 + 「需下载」'],
    ['操作区', '确认领取按钮', '蓝色主按钮，点击后触发领取'],
    ['进度预览面板', '进度条 + 状态信息', '任务开始处理后显示实时进度'],
]
add_table(layout_headers, layout_rows_42)

# 4.3
add_heading_styled('4.3 部门共享库', level=2)
add_body_text('页面概述：展示本部门的共享成果列表，支持搜索和筛选。', bold=True)

layout_rows_43 = [
    ['顶部搜索栏', '关键词搜索输入框', '按文件名/标题搜索'],
    ['筛选区', '部门筛选下拉框', '按来源部门筛选（管理员可见多个部门）'],
    ['筛选区', '格式筛选标签组', '按文件格式（json/markdown/text/image）筛选'],
    ['视图切换', '列表 / 网格切换按钮', '切换列表展示或网格卡片展示'],
    ['成果卡片', '标题 + 部门 + 格式 + 时间', '成果文件的基本信息'],
    ['成果卡片', '下载按钮', '点击下载共享成果文件'],
    ['底部分页', '分页器', '支持多页浏览'],
]
add_table(layout_headers, layout_rows_43)

# 4.4
add_heading_styled('4.4 管理后台', level=2)
add_body_text('页面概述：管理员和部门主管的管理控制台。', bold=True)

layout_rows_44 = [
    ['左侧菜单（深色背景）', '模型配置', '管理模型注册表（增删改查）'],
    ['左侧菜单（深色背景）', '部门锁定', '任务类型 × 部门矩阵的模型锁定配置'],
    ['左侧菜单（深色背景）', '配额设置', '计算配额 + 费用配额 + 用户限流'],
    ['左侧菜单（深色背景）', 'Agent 管理', '在线/离线/suspected Agent 列表'],
    ['左侧菜单（深色背景）', '数据看板', '任务、成本、节点大盘'],
    ['右侧内容区', '模型配置表格', '展示所有模型及其配置参数'],
    ['右侧内容区', '全局参数设置', '系统级参数配置表单'],
]
add_table(layout_headers, layout_rows_44)

# 4.5
add_heading_styled('4.5 个人设置', level=2)
add_body_text('页面概述：用户个人资料和 Agent 配置管理。', bold=True)

layout_rows_45 = [
    ['左侧菜单', '个人资料', '编辑头像、姓名、部门、邮箱'],
    ['左侧菜单', '密码', '修改登录密码'],
    ['左侧菜单', 'Agent 配置', '本地模型路径、API Key 配置'],
    ['左侧菜单', '通知偏好', '通知渠道开启/关闭'],
    ['右侧表单区', '头像头像上传', '点击上传新头像'],
    ['右侧表单区', '姓名/部门/邮箱输入框', '用户基本信息编辑'],
    ['右侧表单区', 'API Keys 管理', '第三方 API Key 配置（敏感信息加密存储）'],
    ['右侧表单区', '模型路径设置', '本地模型文件路径配置'],
]
add_table(layout_headers, layout_rows_45)

# 4.6
add_heading_styled('4.6 站内消息中心', level=2)
add_body_text('页面概述：导航栏铃铛图标点击后展开的消息中心浮层。', bold=True)

layout_rows_46 = [
    ['导航栏', '铃铛图标（未读小红点）', '显示未读消息数量，有新消息时闪烁'],
    ['下拉面板', 'Tab：全部 / 未读 / 系统 / 任务', '按分类筛选通知'],
    ['下拉面板', '通知卡片列表', '图标 + 标题 + 时间 + 已读/未读状态'],
    ['下拉面板', '全部标记已读按钮', '一键将所有通知标记为已读'],
    ['底部', '查看全部消息', '跳转到消息中心完整页面'],
]
add_table(layout_headers, layout_rows_46)

add_page_break()

# ============================================================
# 五、交互逻辑
# ============================================================
add_heading_styled('五、交互逻辑', level=1)
add_body_text('交互流程图文件参考：E:/project/openclaw-platform/07-interaction-flow.excalidraw')

add_heading_styled('5.1 页面流转表', level=2)
flow_headers = ['从', '到', '触发条件', '权限']
flow_rows = [
    ['登录页', '我的任务', '登录成功', '所有用户'],
    ['任务卡片', '任务详情', '点击卡片', '所有用户'],
    ['任务详情', '领取确认', '点击领取按钮', '所有用户'],
    ['领取确认', '进度看板', '点击「开始处理」', '已领取员工'],
    ['进度看板', '成果提交', 'Agent 自动完成', '系统'],
    ['我的任务', '共享库', '导航切换', '所有用户'],
    ['我的任务', '管理后台', '导航切换', '管理员/主管'],
    ['管理后台', '子页面', '左侧菜单点击', '管理员/主管'],
    ['我的任务', '个人设置', '导航切换', '所有用户'],
    ['任意页面', '消息中心', '铃铛点击（浮层）', '所有用户'],
]
add_table(flow_headers, flow_rows)

add_heading_styled('5.2 前端 WS 断连策略', level=2)
ws_headers = ['场景', '前端行为']
ws_rows = [
    ['WS 正常', '实时接收任务状态推送'],
    ['WS 断连', '头部显示黄色横幅「连接已断开，显示数据可能有延迟」'],
    ['WS 断连中', '任务列表显示上次快照时间，按钮保持可用'],
    ['WS 重连成功', '自动刷新全量数据，横幅消失'],
    ['WS 重连失败（>30 秒）', '红色横幅「连接异常，请刷新页面」'],
]
add_table(ws_headers, ws_rows)

add_heading_styled('5.3 任务状态机流转', level=2)
add_body_text('V2.2 更新版（含自动兜底路径）：')
state_text = '''待分配 ─→ 已领取
  │                   │
  └──→ 已分配(auto) ──┘    ← 自动兜底分配的路径
        │
        ↓
      处理中 → 已完成
         ↘ 失败 → 重试中 → 重试成功 → 已完成
                           ↘ 已达上限 → 死信队列 → 人工介入'''
p = doc.add_paragraph()
run = p.add_run(state_text)
set_run_font(run, name='Consolas', size=Pt(9))

add_body_text('说明：', bold=True)
add_body_text('• 手动领取路径：待分配 → 已领取（员工点击领取，claimed_at = NOW()）')
add_body_text('• 自动兜底分配路径：待分配 → 已分配(auto)（系统自动分配，与手动领取后的最终状态一致）')
add_body_text('• 两条路径在已领取/已分配(auto) 状态汇合，后续超时释放规则相同')
add_body_text('• 已领取状态持续 30 分钟 → 员工未点「开始处理」→ 自动释放回待分配 + 记异常日志')

add_page_break()

# ============================================================
# 六、API 接口定义
# ============================================================
add_heading_styled('六、API 接口定义', level=1)
add_body_text('本章节为 API 接口概要说明，详细完整定义请参见 api-definition.md 文档。')

api_headers = ['接口组', '端点', '核心功能']
api_rows = [
    ['1. 任务管理 API', '/api/v1/tasks', '创建任务、获取任务列表/详情、领取、开始处理、进度上报、成果提交、离线提交、释放任务'],
    ['2. 模型管理 API', '/api/v1/models', '模型注册表 CRUD、模型路由决策'],
    ['3. 部门/配额 API', '/api/v1/departments', '获取/更新部门配额、锁定/解除模型、获取锁定列表'],
    ['4. 成果共享 API', '/api/v1/shared-results', '分享成果、获取共享列表、审批、下载'],
    ['5. Agent 管理 API', '/api/v1/agents', 'Agent 列表/详情、更新配置、心跳上报'],
    ['6. 审计日志 API', '/api/v1/audit-logs', '审计日志查询（多维度筛选）'],
    ['7. 通知/消息 API', '/api/v1/notifications', '通知列表（V2）、标记已读、全部标记已读'],
    ['8. 管理/看板 API', '/api/v1/dashboard', '任务统计、成本统计、Agent 状态汇总'],
]
add_table(api_headers, api_rows)

add_body_text('认证方式：所有接口（除健康检查等公开端点外）需要在 HTTP Header 中携带 JWT Bearer Token。', bold=True)
add_body_text('基础 URL：https://{panel-domain}/api/v1')
add_body_text('统一响应格式：{request_id, data/error}，分页响应含 items/total/page/page_size')

add_body_text('关键幂等接口：', bold=True)
idem_headers = ['接口', '幂等 Key', '说明']
idem_rows = [
    ['POST /tasks/:id/claim', 'task_id + user_id', '重复请求不会多次分配'],
    ['POST /tasks/:id/submit', 'task_id + version', '重复提交不会重复扣费'],
    ['POST /tasks/:id/progress', 'task_id + progress_seq', '进度上报幂等'],
]
add_table(idem_headers, idem_rows)

add_page_break()

# ============================================================
# 七、数据库设计
# ============================================================
add_heading_styled('七、数据库设计', level=1)

# tasks table
add_heading_styled('7.1 tasks 表', level=2)
tasks_headers = ['字段名', '类型', '说明']
tasks_rows = [
    ['id', 'UUID PRIMARY KEY', '主键'],
    ['title', 'TEXT NOT NULL', '任务标题'],
    ['description', 'TEXT', '任务描述'],
    ['department_id', 'TEXT NOT NULL', '所属部门 ID'],
    ['assignee_id', 'TEXT', '处理人 ID'],
    ['priority', 'INTEGER DEFAULT 3', '优先级：1(紧急)/2(高)/3(普通)/4(低)'],
    ['status', 'TEXT DEFAULT \'pending\'', 'pending/claimed/processing/completed/failed/dead/suspected'],
    ['assignment_strategy', 'TEXT DEFAULT \'manual\'', 'manual/auto/hybrid'],
    ['recommended_model', 'TEXT', '推荐模型'],
    ['override_model', 'TEXT', '员工覆盖选择的模型'],
    ['cache_key', 'TEXT', '缓存 Key（路由缓存）'],
    ['result_url', 'TEXT', '成果文件 URL'],
    ['output_format', 'TEXT', '输出格式：json/markdown/text/image'],
    ['created_at', 'TIMESTAMP DEFAULT NOW()', '创建时间'],
    ['claimed_at', 'TIMESTAMP', '领取时间'],
    ['started_at', 'TIMESTAMP', '开始处理时间'],
    ['completed_at', 'TIMESTAMP', '完成时间'],
    ['claim_timeout_at', 'TIMESTAMP', '30 分钟释放点'],
    ['inactivity_timeout_at', 'TIMESTAMP', '2 小时回收点'],
    ['retry_count', 'INTEGER DEFAULT 0', '重试次数'],
    ['max_retries', 'INTEGER DEFAULT 3', '最大重试次数'],
    ['progress_seq', 'INTEGER DEFAULT 0', '进度上报幂等 Key，每次上报+1'],
    ['suspected_at', 'TIMESTAMP', 'suspected_failure 检测时间'],
    ['created_by', 'TEXT', '创建人'],
    ['created_by_role', 'TEXT', '创建人角色'],
]
add_table(tasks_headers, tasks_rows)

# audit_logs table
add_heading_styled('7.2 audit_logs 表', level=2)
audit_headers = ['字段名', '类型', '说明']
audit_rows = [
    ['id', 'BIGSERIAL PRIMARY KEY', '自增主键'],
    ['actor_id', 'TEXT NOT NULL', '操作人 ID'],
    ['actor_role', 'TEXT NOT NULL', '操作人角色'],
    ['action_type', 'TEXT NOT NULL', '操作类型：create_task/claim_task/submit_task/override_model/lock_model/admin_switch 等'],
    ['target_type', 'TEXT NOT NULL', '目标类型：task/model/department/agent'],
    ['target_id', 'TEXT NOT NULL', '目标对象 ID'],
    ['old_value', 'JSONB', '旧值'],
    ['new_value', 'JSONB', '新值'],
    ['ip_address', 'TEXT', '操作 IP'],
    ['user_agent', 'TEXT', '用户代理'],
    ['created_at', 'TIMESTAMP DEFAULT NOW()', '创建时间'],
]
add_table(audit_headers, audit_rows)

# model_registry table
add_heading_styled('7.3 model_registry 表', level=2)
model_headers = ['字段名', '类型', '说明']
model_rows = [
    ['id', 'UUID PRIMARY KEY', '主键'],
    ['model_name', 'VARCHAR(128) NOT NULL', '模型名称'],
    ['model_type', 'VARCHAR(16) NOT NULL', '模型类型：local/api'],
    ['deploy_location', 'VARCHAR(64)', '部署位置：main/dept_A/dept_B'],
    ['supported_task_types', 'JSONB NOT NULL', '支持的任务类型列表'],
    ['cost_per_call', 'DECIMAL(10,4)', '单次调用费用（元）'],
    ['avg_latency_ms', 'INTEGER', '预估平均延迟（毫秒）'],
    ['status', 'VARCHAR(16) DEFAULT \'online\'', 'online/offline/degraded'],
    ['max_pool_size', 'INTEGER', '并发上限'],
    ['min_ram_gb', 'DECIMAL(4,1)', '最低内存要求（GB）'],
    ['version', 'VARCHAR(32)', '模型版本号'],
    ['created_at', 'TIMESTAMP DEFAULT NOW()', '创建时间'],
]
add_table(model_headers, model_rows)

# department_quotas table
add_heading_styled('7.4 department_quotas 表', level=2)
quota_headers = ['字段名', '类型', '说明']
quota_rows = [
    ['id', 'UUID PRIMARY KEY', '主键'],
    ['department_id', 'TEXT NOT NULL UNIQUE', '部门 ID'],
    ['max_concurrent_tasks', 'INTEGER DEFAULT 10', '计算配额：最大并发任务数'],
    ['max_daily_api_budget', 'DECIMAL(10,2)', '费用配额：日 API 调用预算（¥）'],
    ['max_daily_upload_mb', 'INTEGER DEFAULT 500', '日上传总量（MB）'],
    ['max_user_rate', 'INTEGER DEFAULT 5', '用户级软限流阈值'],
    ['created_at', 'TIMESTAMP DEFAULT NOW()', '创建时间'],
    ['updated_at', 'TIMESTAMP', '更新时间'],
]
add_table(quota_headers, quota_rows)

# shared_results table
add_heading_styled('7.5 shared_results 表', level=2)
share_headers = ['字段名', '类型', '说明']
share_rows = [
    ['id', 'UUID PRIMARY KEY', '主键'],
    ['task_id', 'UUID NOT NULL', '来源任务 ID（外键）'],
    ['source_department_id', 'TEXT NOT NULL', '来源部门 ID'],
    ['target_department_id', 'TEXT', '目标部门 ID'],
    ['target_user_id', 'TEXT', '目标用户 ID'],
    ['approval_status', 'TEXT DEFAULT \'pending\'', 'pending/approved/rejected'],
    ['approved_by', 'TEXT', '审批人'],
    ['file_url', 'TEXT NOT NULL', '成果文件 URL'],
    ['file_hash', 'TEXT', '文件 SHA256 哈希'],
    ['output_format', 'TEXT', '输出格式'],
    ['created_at', 'TIMESTAMP DEFAULT NOW()', '创建时间'],
]
add_table(share_headers, share_rows)

add_page_break()

# ============================================================
# 八、技术架构
# ============================================================
add_heading_styled('八、技术架构', level=1)

add_heading_styled('8.1 部署架构', level=2)
add_body_text('系统部署层次关系（从外到内）：')
arch_text = '''Nginx（TLS 终止 + 反向代理）
  │
  ├──→ NATS JetStream（消息队列，JWT 认证 + 部门 topic 隔离）
  │     ├──→ PostgreSQL DB（任务、用户、审计、配额）
  │     ├──→ MinIO 对象存储（文件、模型、成果）
  │     └──→ Redis（心跳、缓存、令牌）
  │
  ├──→ FastAPI（调度 + 路由 + API 网关）
  │
  ├──→ Web Panel（React + Ant Design Pro）
  │
  └──→ Agent（员工本地，通过 NATS WS + HTTP 连接）'''
p = doc.add_paragraph()
run = p.add_run(arch_text)
set_run_font(run, name='Consolas', size=Pt(9))

add_body_text('数据隔离方案：', bold=True)
add_body_text('• DB 层面：所有表通过 department_id 字段隔离，单库单 schema')
add_body_text('• 文件层面：MinIO 按 bucket/{department_id}/ 目录隔离')
add_body_text('• API 层面：后端 WHERE dept_id = current_user.dept_id + 行级权限')

add_heading_styled('8.2 技术栈', level=2)
tech_headers = ['组件', '方案', '理由']
tech_rows = [
    ['主框架', 'FastAPI (Python)', '异步、自动 OpenAPI、生态好'],
    ['消息队列', 'NATS + JetStream', '20MB 二进制，持久化，WS 原生支持'],
    ['数据库', 'PostgreSQL', '结构化数据 + JSONB'],
    ['心跳/缓存', 'Redis', '心跳写 Redis（TTL 60s），状态变更写 PG'],
    ['对象存储', 'MinIO', 'S3 兼容，开源，轻量'],
    ['前端', 'React + Ant Design Pro', '后台管理效率高'],
    ['状态管理', 'Zustand', '轻量，跨 Tab 共享'],
    ['移动端', 'Ant Design Mobile + PWA', '管理层手机看板'],
    ['分节点 Agent', 'Python', '跨平台，批量回报'],
    ['编排', 'Docker Compose → K3s', 'MVP 用 Compose，后续升 K3s'],
]
add_table(tech_headers, tech_rows)

add_heading_styled('8.3 安全方案', level=2)
add_body_text('1. NATS JWT 认证：所有 Agent 连接时需携带凭证，NATS 原生 Account/User 的 subs/pub 权限声明限制每个 Agent 只能订阅/发布本部门 topic')
add_body_text('2. Nginx TLS 终止：前端通过 wss://面板域名/ws/nats 连接，Nginx 做 TLS 终止 + 身份透传')
add_body_text('3. 权限 middleware：API 层通过 JWT 解析用户角色，数据层面通过 department_id 做行级权限隔离')
add_body_text('4. Redis 兜底：Agent 连续 3 次 Redis 写入失败 → 降级为直接 POST 到主节点 API 写 PG')

add_body_text('资源限制：', bold=True)
add_body_text('• Docker 各容器设置 --memory 限制：PG 1GB、Redis 512MB、NATS 256MB、MinIO 512MB、FastAPI 512MB、Nginx 128MB')
add_body_text('• 持久化路径：JetStream 和 PG 分别映射到不同磁盘目录，避免 I/O 争抢')
add_body_text('• 数据库备份：每日 pg_dump → MinIO 对象存储，保留最近 7 天')

add_page_break()

# ============================================================
# 九、错误场景
# ============================================================
add_heading_styled('九、错误场景', level=1)

add_heading_styled('9.1 网络断开场景', level=2)
net_headers = ['场景', '系统行为']
net_rows = [
    ['Agent 断网', '本地 SQLite 缓存继续执行，恢复联网后先拉取任务状态再提交'],
    ['Agent 断网 > 90s', '标记 suspected_failure，通知管理员'],
    ['Agent 断网 > 120s', '主节点标记 Stale，已分配任务自动释放'],
    ['主节点 NATS 宕机', 'JetStream 持久化保证消息不丢，重启后恢复消费'],
    ['提交成果中断网', '文件半上传 → MinIO 存储不完整 → 重连后通过 hash 校验重新上传'],
    ['Agent 恢复联网发现任务已被重分配', '本地缓存结果丢弃，写入本地日志 + 系统通知：「任务 #xxx 已被其他同事处理」'],
]
add_table(net_headers, net_rows)

add_heading_styled('9.2 任务异常场景', level=2)
task_err_headers = ['场景', '系统行为']
task_err_rows = [
    ['领取后 30 分钟未开始', '自动释放回待分配池，记异常日志'],
    ['领取后 2 小时无更新', '自动回收 + 通知管理员'],
    ['模型调用失败', '自动降级到备用模型，日志记录降级链路（超时 30s→重试 1 次→fallback）'],
    ['所有模型都失败', '任务进死信队列，通知管理员人工处理'],
    ['员工本地没装推荐模型', 'Agent 检测 → 自动 fallback 到 API 模型 → 任务卡片显示提示信息'],
]
add_table(task_err_headers, task_err_rows)

add_heading_styled('9.3 并发冲突场景', level=2)
con_headers = ['场景', '措施']
con_rows = [
    ['两个员工同时领取同一任务', 'Redis 分布式锁，保证一个成功'],
    ['自动分配与手动领取冲突', '同一把分布式锁，后到返回失败'],
    ['任务重复提交', '全局 task_id 去重 + version 字段，结果覆盖不重复计费'],
]
add_table(con_headers, con_rows)

add_page_break()

# ============================================================
# 十、成本测算
# ============================================================
add_heading_styled('十、成本测算', level=1)

add_heading_styled('10.1 固定成本', level=2)
fixed_headers = ['项目', '月费用', '说明']
fixed_rows = [
    ['云服务器 4C8G（主节点）', '¥200-300', '阿里云/腾讯云轻量级 ECS'],
    ['云服务器 2C4G（测试环境）', '¥50', '独立测试环境'],
    ['MinIO 存储 100GB', '¥30', '对象存储费用'],
    ['NATS 开源免费', '¥0', '开源'],
    ['域名 + SSL', '¥20', '每年 ¥200-300'],
    ['合计', '¥300-400/月', ''],
]
add_table(fixed_headers, fixed_rows)

add_heading_styled('10.2 可变成本（模型调用）', level=2)
var_headers = ['部门', '使用模式', '月预估费用']
var_rows = [
    ['研发部（10人）', '本地 7B 量化免费 + 深度推理 API 偶发', '¥0 + ¥30-80'],
    ['市场部（5人）', 'API 文案生成，约 500 次/月', '¥15-25'],
    ['人事部（3人）', '本地小模型 + API 少量', '¥5-10'],
    ['模型月费合计', '', '¥50-115'],
]
add_table(var_headers, var_rows)

add_heading_styled('10.3 降本测算对比', level=2)
saving_headers = ['场景', '独立部署', '统一平台', '节省']
saving_rows = [
    ['算力', '每部门各买 GPU', '共享本地模型池', '60-70%'],
    ['API 调用', '各买各的 token', '集中采购按量分配', '30-40%'],
    ['重复任务', '无法利用他人结果', '结果缓存命中', '20-30%'],
    ['总降本', '', '', '30-50%'],
]
add_table(saving_headers, saving_rows)

add_body_text('注：对比基线为各部门独立部署（GPU 服务器 + 各自买 API token ≈ ¥800-1500/月）。')

# ============================================================
# Add header/footer
# ============================================================
for section in doc.sections:
    # Header
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = hp.add_run('OpenCLAW 协作系统 PRD · V2.2')
    set_run_font(run, name='微软雅黑', east_asia='微软雅黑', size=Pt(8), color=RGBColor(0x66, 0x66, 0x66))

    # Footer with page number
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run('第 ')
    set_run_font(run, name='微软雅黑', east_asia='微软雅黑', size=Pt(8), color=RGBColor(0x66, 0x66, 0x66))

    # Add PAGE field
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    run2 = fp.add_run()
    run2._r.append(fldChar1)
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
    run3 = fp.add_run()
    run3._r.append(instrText)
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run4 = fp.add_run()
    run4._r.append(fldChar2)

    run5 = fp.add_run(' 页')
    set_run_font(run5, name='微软雅黑', east_asia='微软雅黑', size=Pt(8), color=RGBColor(0x66, 0x66, 0x66))

# ============================================================
# Save
# ============================================================
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
doc.save(OUTPUT_PATH)
print(f"✅ PRD document saved to: {OUTPUT_PATH}")
