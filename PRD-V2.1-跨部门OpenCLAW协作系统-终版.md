# PRD V2.2（PM终审版）：跨部门 OpenCLAW 协作系统

**版本**：V2.2 · PM 终审版
**产品经理**：老高（PM）
**日期**：2026-05-25
**状态**：全员第四轮意见整合完毕，待高总审批后进入开发

---

## 一、修订说明

本版本基于 V2.1 全员第三轮评审意见（Reviewer 3 条 + Backend 4 条 + PM 自查 1 条）逐条修订。

| # | 提出人 | 问题 | 修改位置 |
|---|-------|------|---------|
| 1 | Reviewer | NATS WS 安全 + 反向代理 | 决策1 + 架构图 |
| 2 | Reviewer | timeout_at 字段语义冲突 | §7 tasks 表 |
| 3 | Reviewer | 自动兜底与 assignment_strategy 矛盾 | §4.1 |
| 4 | Reviewer | 「默认强制」措辞矛盾 | 决策4 |
| 5 | Reviewer | 深度推理成本漏算 | §10.2 |
| 6 | Reviewer / Deploy | 灰度方案不清晰 | §4.5 + §9 |
| 7 | Reviewer | Agent 重连策略未定义 | §4.2 |
| 8 | Reviewer / Architect | 权限模型缺失 | 新增权限章节 |
| 9 | Frontend | Web 面板工作流断点 | §8.1 |
| 10 | Frontend | 页面清单 + 导航结构缺失 | 新增 §8.4 |
| 11 | Frontend | 三级模型 UI 层级冲突 | §8.1 |
| 12 | Frontend | 共享库 UI 形态未定义 | §8.4 |
| 13 | Frontend | 前端 WS 断连兜底 | 新增 §8.5 |
| 14 | Frontend | 模型缺失的 UI 反馈 | §8.1 |
| 15 | Frontend | 管理员锁配置界面 | §8.4 |
| 16 | Tester | Agent 崩溃 120s 静默窗口 | §4.2 |
| 17 | Tester | 离线模式任务两端冲突 | §5.1 |
| 18 | Tester | 成果文件 MD5 校验 | §6 |
| 19 | Tester | 用户级限流 | §4.3 |
| 20 | Tester | 模型可用性检测职责 | §4.2 + §4.3 |
| 21 | Tester | 统一审计日志 | 新增 audit_logs 表 |
| 22 | Tester | 通知机制盲区 | §8.6 |
| 23 | Tester | 测试环境搭建时间 | §9 |
| 24 | Deploy | Agent 更新机制 MVP 就做 | §4.2 |
| 25 | Deploy | NATS 认证 + 资源限制 | 决策1 + §11 |
| 26 | Deploy | Redis 兜底策略 | §3.3 |
| 27 | Deploy | Docker Compose 细节 | §11 |
| 28 | Deploy | Prometheus/Grafana 具体方案 | §4.5 |
| 29 | Deploy | 灰度回滚方案 | §4.5 + §9 |
| 30 | Deploy | 文件上传约束 | §4.4 |
| 31 | Backend | 手动领取 + 自动兜底锁 | §4.1 |
| 32 | Backend | 进度上报走 NATS Pub/Sub | §4.2 |
| 33 | Backend | 文件上传大小和限流 | §4.4 |
| 34 | Backend | fallback 链触发条件 | §4.3 |
| 35 | Backend | 离线缓存队列冲突 | §5.1 |
| 36 | Backend | 完整 DDL | §7 |
| 37 | Architect | 同机资源争抢 | §3.1 + §11 |
| 38 | Architect | 数据库备份策略 | §3.1 |
| 39 | Architect | 兜底分配判定标准 | §4.1 |
| 40 | Architect | 配额双层计费 | §4.3 |
| 41 | Architect | 成本数据来源 | §4.3 |
| 42 | Architect | Agent 模型执行器映射 | §4.2 |
| 43 | Architect | 离线上传完整链路 | §5.1 |
| 44 | Architect | 数据隔离粒度 | §3.1 |
| 45 | Architect | 管理员锁热更新 | §4.3 |
| 46 | Architect | 日志采集方案 | §4.5 |
| — | — | — | — |
| **V2.2 新增（第三轮评审）** | | |
| 47 | Reviewer | Nginx 做部门 topic 校验不成立 → 改为 NATS JWT 认证 + Nginx 透传 | 决策 1 |
| 48 | Reviewer | progress_seq 字段接口中有但表里缺 → 加字段 | §9.1 |
| 49 | Reviewer | 站内消息数据表未定义 → 说明 MVP 存储方案 | §10.6 |
| 50 | Backend | 状态机缺自动兜底分配路径 → 补虚线路径 + 说明 | §6.1 |
| 51 | Backend | 离线丢弃结果员工不知情 → 加系统通知 + 日志 | §7.1 |
| 52 | Backend | fallback 链总超时过长 → 收紧至 15s/30s | §6.3 |
| 53 | Backend | 模型下载无带宽控制 → 加 Redis 分布式锁 | §6.2 |
| 54 | PM（自查） | Nginx WS proxy_read_timeout + worker_connections 未配 → 补配置示例 | 决策 1 |

---

## 二、产品背景与目标

### 2.1 背景
中小型企业内部多部门使用 OpenCLAW 进行 AI 任务处理，但存在痛点：
- 各部门各自部署 OpenCLAW，模型重复采购，GPU 资源浪费
- 跨部门协作没有统一平台，任务流转靠口头/群聊，不可追踪
- 高价值大参数模型不是所有部门都买得起/跑得动
- 缺乏统一的任务进度管理和成果共享机制

### 2.2 目标
构建**轻量级、低成本、可插拔**的跨部门 OpenCLAW 协作平台，实现：
1. 主-分节点统一调度：任务下发 → 执行 → 回传全流程闭环
2. 模型统一管理，按部门按任务类型自动路由最优性价比模型
3. 任务进度实时可见，成果一键共享
4. **首月降本 30%**（模型调用共享池化，结果缓存降低重复计算）

### 2.3 目标用户

| 角色 | 典型用户 | 核心需求 |
|------|---------|---------|
| 系统管理员 | IT主管 | 节点管理、模型配置、数据看板、配额设置 |
| 部门主管 | 研发/市场/人事负责人 | 分配任务、看部门工单、看成本统计、锁定模型范围 |
| 普通员工 | 研发工程师/文案/HR | 领取任务、执行、提交成果、查看共享库 |

---

## 三、关键决策（全员评审结论）

### 决策 1：连接方案 → NATS + JetStream

**最终结论：NATS JetStream（全员一致通过）**

| 维度 | NATS | RabbitMQ | Redis Streams |
|------|------|----------|---------------|
| 二进制大小 | ~20MB | ~150MB + Erlang VM | 依赖 Redis（~30MB） |
| 内存占用 | 空闲 ~5MB | 空闲 ~50MB+ | 取决于用途 |
| 部署复杂度 | 单文件启动 | 需配 Erlang 环境 | 需额外装 Redis |
| 持久化 | ✅ JetStream | ✅ 完善 | ✅ RDB/AOF |
| ACK 机制 | ✅ at-least-once | ✅ 完善 | ✅ 需手写 |
| 前端 WS 原生支持 | ✅ 原生 | ❌ 需额外网关 | ❌ 需自己封装 |
| 运维成本 | 低 | 高 | 中 |

**⚠️ 强制配置（Reviewer + Deploy 要求）：**

**安全配置：**
1. **NATS WS 端口不暴露公网**，前端和 NATS 之间加 **Nginx 反向代理层**
2. **NATS JWT/Nkeys 认证**：所有 Agent 连接时需携带凭证，未认证连接拒绝；NATS 原生 Account/User 的 `subs`/`pub` 权限声明限制每个 Agent 只能订阅/发布本部门 topic
3. 前端通过 **wss://面板域名/ws/nats** 连接到 Nginx，Nginx 做 **TLS 终止 + 身份透传**（通过 `proxy_set_header X-NATS-User $http_authorization` 向后传递 JWT），NATS 层面做 topic 权限校验，**Nginx 不负责判断 topic 归属**

**持久化配置：**
4. **必须开 JetStream**：NATS 默认内存模式，不开持久化主节点挂了队列全丢
5. **at-least-once + 手动 ACK**：分节点处理完才 ACK，避免消费中途挂掉任务消失

**资源限制（Deploy 要求）：**
6. JetStream 配置：`max_msg_size=10MB`、`max_msgs_per_stream=100000`、`max_bytes_per_stream=1GB`
7. 磁盘使用率 > 85% 触发告警

**Nginx WS 代理配置（PM 自查补充）：**

```nginx
# 关键参数
proxy_read_timeout 60s;     # WS 长连接超时，超过 60s 无数据自动断连
worker_connections 1024;    # 50 员工 × 2 连接（WS + HTTP）= 100，留余量

# 完整 location 示例
location /ws/nats/ {
    proxy_pass http://127.0.0.1:9222/;  # NATS WS 端口
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}
```

### 决策 2：服务器规格 → 4C8G 轻量云起步

MVP 阶段用 2C4G 当心 MQ + Web 面板 + 数据库三者同时跑时撑不住。**起步用 4C8G**（阿里云/腾讯云轻量云约 ¥200-300/月），后续上 Docker Compose 编排，扩缩容一条命令搞定。

### 决策 3：任务分配 → 手动领取为主 + 自动兜底

**全员结论：MVP 手动领取，但必须做以下机制：**

1. **手动领取（MVP 核心）**：员工在 Web 面板上看到待领取任务列表，主动点击领取
2. **30 分钟超时自动释放**：员工领取后超过 30 分钟不点「开始处理」，任务自动回到待领取池，并记录异常日志
3. **自动兜底分配**：
   - `assignment_strategy = 'manual'` 的任务**永远不触发自动兜底**，等人工领取
   - `assignment_strategy = 'auto'` 或 `'hybrid'` 的任务，10 分钟无人领取时触发自动兜底
   - 判定标准（Architect 要求）：按 Agent 上报的 `current_concurrency / max_concurrency` 比例排序，比例最低的优先分配
4. **分布式锁**：手动领取和自动兜底共享同一把 Redis 分布式锁（Key = `task:lock:{task_id}`，TTL = 10 秒）。谁先抢到锁谁改状态，后到的一方返回「任务已被领取」
5. **数据库字段预留**：任务表增加 `assignment_strategy` 字段（`manual` / `auto` / `hybrid`）

### 决策 4：模型路由 → 三级模型选择机制

**最终方案：**

```
第一级（默认自动）：主节点自动路由，默认走最便宜的模型
  ├── 模型路由表按「任务类型 + 部门」自动匹配
  ├── 例如：文档摘要 → qwen2.5-7b（本地，¥0），代码审查 → deepseek-coder-7b（本地，¥0）
  └── 降本核心：默认不走贵模型，除非用户显式要求

第二级（员工可选覆盖）：提交/领取任务时可选「换模型」
  ├── 下拉框显示可用模型清单
  │   ├── 如果管理员锁定了模型 → 下拉框 disabled，tooltip：「该模型由管理员锁定」
  │   ├── 如果员工本地没安装该模型 → 灰色显示，标注「需下载」
  │   └── 如果员工本地没装任何模型 → 标红提示「您本地无此模型，将使用 API 版本」
  ├── 旁边显示成本对比：「推荐模型：¥0.03/次 │ 您选择：¥0.15/次」
  │   └── 成本数据从模型注册表动态获取，非硬编码
  ├── 选了贵的，弹窗确认「成本警告」，但不强制拦截
  └── 后端记录每次模型选择日志

第三级（管理员锁）：部门主管可锁定某些任务的模型范围
  ├── 锁定后：新任务默认走锁定模型
  ├── 已分配但未执行的任务：保持原选择不强制重置
  ├── 管理员可在 Web 面板一键切换全部门默认模型
  └── 配置变更通过 NATS 推送热生效，所有 Agent 收到后重新加载模型路由表
```

**硬规矩：** 自动路由默认永远走**成本最低**的可用模型。只有任务里显式勾选了「需要高精度推理」，才走贵模型。

**模型路由可追溯：** 每次 auto 路由决策记录日志：
```json
{
  "route_decision": {
    "task_id": "xxx",
    "input_type": "文档摘要",
    "recommended_model": "qwen2.5-7b",
    "reason": "任务类型=文档摘要，部门=市场部，默认路由到本地小模型",
    "cost_saved": "¥0.12"
  }
}
```

---

## 四、Agent 与 OpenCLAW 的物理关系（PM 自查补充）

```
┌─────────────────────────────────────────────────────┐
│                  员工本地环境                        │
│                                                     │
│  ┌────────────────┐  ┌────────────────────────┐     │
│  │  OpenCLAW GUI  │  │  分节点 Agent (Python)  │     │
│  │ (可选桌面应用)  │←→│  - 连接主节点 MQ        │     │
│  │ 用于手动调试   │  │  - 拉取任务             │     │
│  │ 查看模型输出   │  │  - 调用本地模型/API     │     │
│  └────────────────┘  │  - 上报进度             │     │
│                       │  - 上传成果             │     │
│                       │  - 离线缓存 (SQLite)    │     │
│                       │  - 自动更新             │     │
│                       └────────────────────────┘     │
│                                  │                   │
│                       ┌──────────▼─────────┐         │
│                       │  本地模型引擎        │         │
│                       │ (Ollama/llama.cpp)  │         │
│                       └────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

**关键规则：**
- Agent 是**常驻后台服务**，负责所有与主节点的通讯
- OpenCLAW GUI 是可选前端，员工也可以通过它手动提交任务给 Agent
- **MVP 模式**：员工在 Web 面板领取任务 → Agent 自动执行 → 员工在 Web 面板查看结果
- Agent 自动更新（MVP 就做）：Agent 启动时检查主节点 `/agent/version/latest`，对比本地版本号，有更新则在后台静默下载，下次重启时替换

### 模型部署策略

| 问题 | 回答 |
|------|------|
| 谁装本地模型？ | IT 统一部署，模型文件从主节点 MinIO 下发，Agent 启动时自动检测并下载缺失模型 |
| 没 GPU 的机器？ | 自动 fallback 到 API 模式，或在 CPU 上慢速运行 |
| 模型文件存哪？ | Agent 本地缓存（量化模型约 4GB/个），每个员工只下载自己部门需要的模型 |
| 模型文件校验？ | Agent 启动时校验本地文件 hash，不一致则重新下载 |

### 文件格式兼容性

不同模型输出格式不同，系统不做自动格式转换。
- 成果共享时，发送方标注「输出格式」字段（json / markdown / text / image）
- 接收方查看时按原格式展示
- V2 再加格式转换器

### 跨部门共享审批流程

- **同部门**：自动归档到共享库，无需审批
- **跨部门分享**：A 部门员工点击「分享到 B 部门」→ 系统发送通知给 B 部门主管 → B 主管接收后入库
- **跨部门查看**：B 部门只能看到 A 部门主动分享的成果，看不到 A 部门的完整共享库

### V2 路线图

| 里程碑 | 条件 | 内容 |
|--------|------|------|
| MVP（第 0-14 天） | — | 手动领取、Web 面板、3 个部门试用 |
| V1.1（第 15-30 天） | 日均任务 > 50 | Agent 全自动模式、跨部门转派、邮件通知 |
| V1.2（第 31-60 天） | 日均任务 > 100 | 自动分配算法优化、故障演练、格式转换 |
| V2（第 61-90 天） | ROI 为正 | OpenTelemetry 全链路追踪、多集群高可用 |

---

## 五、系统架构

### 5.1 部署架构（V2.1 更新版）

```
┌──────────────────────────────────────────────────────────────┐
│                      ☁️ 云服务器（4C8G）                       │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Nginx 代理   │  │ NATS JetStream│  │  MinIO 对象存储  │   │
│  │ (TLS+鉴权)   │←→│ (JWT认证+持久 │←→│ (文件/模型/成果) │   │
│  ├──────────────┤  │  化+资源限制) │  ├──────────────────┤   │
│  │  FastAPI API  │  ├──────────────┤  │  Redis           │   │
│  │ (调度+路由)   │←→│ PostgreSQL DB │←→│ (心跳+缓存+令牌) │   │
│  ├──────────────┤  │ (任务/用户/   │  └──────────────────┘   │
│  │  Web 面板     │  │  审计/配额)  │                          │
│  │ (React+AntD) │  └──────────────┘                          │
│  └──────────────┘                                            │
└──────────────────────┬───────────────────────────────────────┘
                       │ WireGuard VPN / 公网 TLS
          ┌────────────┼────────────────┐
          │            │                │
  ┌───────▼────┐  ┌───▼────┐   ┌──────▼──────┐
  │ 研发部 K3s  │  │市场部 PC│   │ 人事部 PC   │
  │ ┌────────┐ │  │┌──────┐│   │┌───────────┐│
  │ │ 分Agent │ │  ││分Agent││   ││ 分Agent   ││
  │ │ +本地7B  │ │  ││+API直调││   ││+本地小模型 ││
  │ │ (量化)   │ │  ││(买token)│  ││ (量化4bit)││
  │ └────────┘ │  │└──────┘│   │└───────────┘│
  └────────────┘  └───────-┘   └──────────────┘
```

**数据隔离粒度（Architect 要求）：**
- **DB 层面**：所有表通过 `department_id` 字段隔离，单库单 schema
- **文件层面**：MinIO 按 `bucket/{department_id}/` 目录隔离
- **API 层面**：后端 `WHERE dept_id = current_user.dept_id` + 行级权限

**资源限制（Architect 要求）：**
- Docker 各容器设置 `--memory` 限制：PG 1GB、Redis 512MB、NATS 256MB、MinIO 512MB、FastAPI 512MB、Nginx 128MB
- 持久化路径：JetStream 和 PG 分别映射到不同磁盘目录，避免 I/O 争抢

**数据库备份：** 每日 pg_dump → MinIO 对象存储，保留最近 7 天

### 5.2 技术栈（V2.0 保持一致）

| 组件 | 方案 | 理由 | 来源 |
|------|------|------|------|
| 主框架 | FastAPI (Python) | 异步、自动 OpenAPI、生态好 | PM |
| 消息队列 | NATS + JetStream | 20MB 二进制，持久化，WS 原生 | 全员一致 |
| 数据库 | PostgreSQL | 结构化数据 + JSONB | PM |
| 心跳/缓存 | Redis | 心跳写 Redis（TTL 60s），状态变更写 PG | Reviewer |
| 对象存储 | MinIO | S3 兼容，开源，轻量 | PM |
| 前端 | React + Ant Design Pro | 后台管理效率高 | PM + Frontend |
| 状态管理 | Zustand | 轻量，跨 Tab 共享 | Frontend |
| 移动端 | Ant Design Mobile + PWA | 管理层手机看板 | Frontend |
| 分节点 Agent | Python | 跨平台，批量回报 | PM |
| 编排 | Docker Compose → K3s | MVP 用 Compose，后续升 K3s | Deploy |

### 5.3 数据流与心跳设计

```
                    ┌───────────────────┐
                    │     Redis          │ ← 心跳写这里（TTL 60s）
                    │  (agent_heartbeat) │    50 员工 × 2880 次/天
                    └────────┬──────────┘     全部放 PG 会炸
                             │ 状态变更才写 PG
                    ┌────────▼──────────┐
                    │   PostgreSQL DB    │ ← 任务状态变更
                    │  (task_status_log) │    只有「待领取→处理中→已完成」
                    └───────────────────┘
```

**核心原则：** 心跳数据高频低价值 → Redis；状态变更低频高价值 → PG。

**Redis 兜底（Deploy 要求）：**
- Agent 每次心跳同时记录到本地日志文件（最后一层兜底）
- 如果 Agent 连续 3 次 Redis 写入失败 → 降级为直接 POST 到主节点 API `/agent/heartbeat-fallback`（写 PG）
- 管理员在 Web 面板可以看到「Redis 异常降级中」的告警标签

---

## 六、功能模块

### 6.1 模块一：任务管理

| 功能 | 描述 | MVP | 来源 |
|------|------|-----|------|
| 创建任务 | 管理员/主管/员工创建，选目标部门、模型、优先级 | ✅ | PM |
| 任务分配 | 自动按空闲度推荐 / 手动指定 | ✅ | PM |
| 任务领取 | 员工在 Web 面板看到待领取任务，一键接单 | ✅ | PM |
| 领取超时释放 | 领取后 30 分钟未开始，自动释放回池 | ✅ | Reviewer + Tester |
| 自动兜底分配 | auto/hybrid 任务 10 分钟无人领 → 自动派给负载最低节点 | ✅ | Architect |
| 任务执行 | 员工本地 Agent 自动执行，进度上报 NATS Pub/Sub | ✅ | PM |
| 任务重试 | 失败自动重试（可配次数），超过进死信队列 | ✅ | Tester |
| 成果提交 | Agent 自动上传（MD5 校验）→ 主管审核 → 归档 | ✅ | PM |
| 任务转派 | 转给另一部门/个人 | V2 | PM |
| 任务自动回收 | 领取后超 2 小时无活动，自动回收通知管理员 | ✅ | Tester |

**任务状态机：**
```
待分配 ─→ 已领取 ←──┐
  │                   │
  └──→ 已分配(auto) ──┘    ← 自动兜底分配的路径
        │
        ↓
      处理中 → 已完成
         ↘ 失败 → 重试中 → 重试成功 → 已完成
                           ↘ 已达上限 → 死信队列 → 人工介入
```

**说明：**
- **手动领取**路径：待分配 → 已领取（员工点击领取，`claimed_at = NOW()`）
- **自动兜底分配**路径：待分配 → 已分配(auto)（系统自动分配，`claimed_at = NOW()`，与手动领取后的最终状态一致）
- 两条路径在 `已领取/已分配(auto)` 状态汇合，后续超时释放规则相同

**领取超时逻辑：**
```
已领取状态持续 30 分钟 → 员工未点「开始处理」→ 自动释放回待分配
                                                     ↘ 记异常日志 (claim_timeout)
```

**权限模型（Reviewer + Architect 要求）：**

| 操作 | 管理员 | 部门主管 | 普通员工 |
|------|--------|---------|---------|
| 创建任务（本部门） | ✅ | ✅ | ✅ |
| 创建任务（跨部门） | ✅ | ✅ | ❌ |
| 领取任务 | ✅ | ✅ | ✅ |
| 修改模型 | ✅ | ✅ | ✅（自己领的任务） |
| 锁定部门模型 | ✅ | ✅（本部门） | ❌ |
| 查看其他部门共享库 | ✅ | ❌ | ❌ |
| 删除任务 | ✅ | ✅（本部门） | ❌ |

权限校验在 API 层用 middleware 实现。

### 6.2 模块二：员工分节点 Agent

| 能力 | 说明 | MVP |
|------|------|-----|
| 连接主节点 | 启动时 NATS 注册，JWT 验证部门+身份 | ✅ |
| 心跳上报 | 每 30 秒上报存活 + 并发数 + 资源占用（→ Redis） | ✅ |
| 模型可用性上报 | 启动时上报本地模型清单 + 显存/内存使用率 | ✅ |
| 拉取任务 | 主动从 NATS 队列拉取分配给自己的任务 | ✅ |
| 资源下载 | 从 MinIO 下载 prompt 模板、参考文档等 | ✅ |
| 任务本地缓存 | Agent 拉到任务后存本地 SQLite，断网也能继续执行 | ✅ |
| 进度上报 | NATS Pub/Sub 到 `task.progress.{task_id}`，前端 WS 实时接收 | ✅ |
| 成果回传 | 执行完成上传 MinIO（含 MD5 校验），返回 result_url | ✅ |
| 断网重连 | 指数退避重连（1s→2s→4s→8s→16s），恢复后批量回传 | ✅ |
| 自动更新 | 启动时检查版本，后台静默下载，下次重启时替换 | ✅（MVP） |
| 模型下载带宽控制 | 从 MinIO 下载本地模型时，通过 Redis 分布式锁（Key=`model.download:{model_name}`，TTL=600s）保证同一时间只有 1 个 Agent 拉取，其他人排队等待；Agent 本地已有模型时通过 hash 校验跳过下载 | ✅（MVP） |

**连接状态机：**

```
Online ──→ Offline ──→ Reconnecting ──→ Online
  │                    │                  │
  │                 Stale (超时)           │
  │                                        │
  └────────────────────────────────────────┘
```

| 状态 | 行为 |
|------|------|
| Online | 正常心跳 + 拉任务 + 执行 |
| Offline | 本地缓存继续执行，不拉新任务 |
| Reconnecting | 指数退避重连：1s→2s→4s→8s→16s，总窗口 ~31s |
| Stale | 心跳超时 > 120s → 主节点标记失联 → 已分配任务自动释放 |
| suspected_failure | 连续 3 次心跳没收（~90s）→ 任务标记告警 → 通知管理员 |

**Agent 模型执行器映射（Architect 要求）：**

Agent 配置文件（`~/.openclaw-agent/config.yaml`）：
```yaml
model_routes:
  qwen2.5-7b:
    executor: local
    model_path: ~/.openclaw-agent/models/qwen2.5-7b-q4.gguf
    min_ram_gb: 4
  deepseek-coder-7b:
    executor: local
    model_path: ~/.openclaw-agent/models/deepseek-coder-7b-q4.gguf
    min_ram_gb: 4
  gpt-4o-mini:
    executor: api
    api_key_env: OPENAI_API_KEY
    endpoint: https://api.openai.com/v1/chat/completions
  doubao:
    executor: api
    api_key_env: DOUBAO_API_KEY
    endpoint: https://api.doubao.com/v1/chat/completions
```

Agent 启动时校验所有 `executor: local` 的模型文件是否存在，不存在则从主节点 MinIO 自动下载。

### 6.3 模块三：模型路由与管理

**模型注册表：**

| 任务类型 | 推荐模型 | 备用模型 | 部署位置 | 成本 |
|---------|---------|---------|---------|------|
| 代码审查 | deepseek-coder-7b (4bit) | gpt-4o-mini | 本地 | ¥0 |
| 文档摘要 | qwen2.5-7b (4bit) | gpt-4o-mini | 本地 | ¥0 |
| 文案生成 | gpt-4o-mini | doubao | API | ¥0.03/次 |
| 翻译 | qwen2.5-7b (4bit) | gpt-4o-mini | 本地 | ¥0 |
| 图像生成 | sd-xl-turbo | — | 本地 GPU | ¥0 |
| 深度推理 | gpt-4o / claude-3 | deepseek-r1 | API | ¥0.15/次 |

**默认路由永远走成本最低的模型。**

**模型降级链（Backend 要求）：**
```
fallback 触发规则：
 第一层（推荐模型）：超时 15s → 重试 1 次（再 15s）→ 仍超时 → fallback
 第二层（备用模型）：超时 30s → 重试 1 次（再 30s）→ 仍超时 → 报错
 第三层（兜底策略）：返回友好错误「模型服务暂不可用，请稍后再试」

总最坏窗口：15+15+30+30 = 90s 以内
```

模型调用失败定义：
- HTTP 超时（推荐模型 15s，备用模型 30s 无响应）
- HTTP 5xx 错误
- 返回结果格式错误（非预期 JSON）
- 返回空结果

**模型路由缓存 Key（Architect 要求）：**
```
cache_key = sha256(task_type + model_name + input_hash + dept_id)
```

**模型配额（Architect + Tester 要求）：**
- **双层配额**：
  - 计算配额：最大并发任务数（本地模型场景）
  - 费用配额：日/月 API 调用预算（¥）（API 调用场景）
- **用户级软限流**：用户超过个人日配额后，任务排队优先级降低（不硬拦 429）
- 超过计算配额 → 任务排队等待
- 超过费用配额 → 返回 429
- Redis Token Bucket，每个部门一个 bucket
- 管理员配置：`研发部 max_tokens/day = 10M` / `max_requests/day = 500`

**成本数据来源（Architect 要求）：**
- 从模型注册表 `cost_per_call` 字段动态获取
- 管理员在 Web 面板更新模型价格后，通过 NATS 推送热生效
- 前端展示时从 API 实时获取

**管理员锁热更新（Architect 要求）：**
- 管理员修改配置 → NATS 推送 → 所有 Agent 收到后重新加载模型路由表
- 配置变更时间边界：新任务走新规则，已分配的任务继续用旧模型

### 6.4 模块四：成果共享

| 功能 | 描述 | MVP |
|------|------|-----|
| 一键分享 | 员工完成→点击「分享」→选同事/部门（同部门自动归档） | ✅ |
| 跨部门分享 | 选对方部门 → 通知对方主管 → 审批后入库 | ✅ |
| 部门共享库 | 自动归档到部门共享 MinIO 目录 | ✅ |
| 共享查看权限 | 按部门隔离，只能看到本部门共享库 + 他部门主动分享的成果 | ✅ |
| 跨部门提交 | 结果作为输入发新任务到另一部门队列 | V2 |

**文件上传约束（Backend + Deploy 要求）：**

| 项目 | MVP 值 |
|------|--------|
| 单文件上限 | 50MB |
| 日上传总量 | 部门配额，管理员可配 |
| 上传失败重试 | 客户端重试 3 次，指数退避 |
| 文件类型白名单 | .md / .json / .txt / .pdf / .png / .jpg / .mp4 < 50MB |
| 文件生命周期 | 超过 30 天自动归档到冷存储 |
| 文件完整性 | 上传前客户端计算 SHA256，服务端校验 |

### 6.5 模块五：监控与运维

| 功能 | 描述 | MVP |
|------|------|-----|
| 任务看板 | 各部门待处理/处理中/完成数 | ✅ |
| Agent 状态 | 在线/离线/suspected_failure Agent 列表 | ✅ |
| 模型成本统计 | 各部门每日/每周模型调用费用 | ✅ |
| 灰度上线 | 先人事部全量试用，观察失败率和延迟 | ✅ |
| Prometheus 指标 | 任务排队数、完成数、失败率、平均耗时 | ✅ |
| OpenTelemetry | 全链路 trace_id 追踪问题 | V2 |
| 压力测试 | 上线前必须过 | ✅ |
| 故障演练 | 模拟节点宕机、网络中断 | V2 |

**Prometheus/Grafana 具体方案（Deploy 要求）：**

| 组件 | Exporter | Grafana 大盘 |
|------|---------|-------------|
| NATS | nats_exporter | 消息吞吐、队列深度、消费延迟 |
| PostgreSQL | postgres_exporter | 连接数、慢查询、缓存命中率 |
| MinIO | minio_exporter | 存储用量、请求延迟 |
| Redis | redis_exporter | 内存使用、命中率、Key 数量 |
| FastAPI | 自定义 metrics | QPS、P50/P95/P99 延迟、错误率 |

**告警规则（MVP 必须）：**
1. NATS 队列深度 > 50 持续 5 分钟 → 通知
2. 任何 Agent 心跳丢失 > 120 秒 → 通知
3. 磁盘使用率 > 85% → 紧急通知
4. 任务失败率 > 5%（1 小时窗口）→ 通知

**日志采集方案（Architect 要求）：**
- MVP 阶段：各服务写本地日志文件（JSON 格式，按天轮转）+ 审计操作写入 `audit_logs` 表
- V2：上 ELK/Loki 集中式日志

---

## 七、错误场景与边界条件

### 7.1 网络断开场景

| 场景 | 系统行为 |
|------|---------|
| Agent 断网 | 本地 SQLite 缓存继续执行，恢复联网后先拉取任务状态再提交 |
| Agent 断网 > 90s | 标记 suspected_failure，通知管理员 |
| Agent 断网 > 120s | 主节点标记 Stale，已分配任务自动释放 |
| 主节点 NATS 宕机 | JetStream 持久化保证消息不丢，重启后恢复消费 |
| 提交成果中断网 | 文件半上传 → MinIO 存储不完整 → 重连后通过 hash 校验，重新上传 |

**离线任务冲突解决（Backend + Tester 要求）：**

```
离线恢复流程：
 1. Agent 恢复联网后，先拉取所有已分配任务的当前状态
 2. 如果任务在主节点上仍标记为 assigned 给本 Agent → 正常提交结果
 3. 如果任务已经被兜底分配给了其他 Agent → 本地缓存的结果丢弃，不提交；**Agent 写入本地日志文件 + 弹出系统通知框：「任务 #xxx 已被其他同事处理，您离线完成的成果未提交」**
 4. 如果任务已经被系统回收（2 小时超时）→ 本地缓存的结果丢弃，提示员工重新领取
```

**离线上传完整链路（Architect 要求）：**

1. 员工离线完成 → 成果存在本地 `~/.openclaw-agent/offline-cache/{task_id}/`
2. 恢复联网后，Agent 遍历离线缓存目录
3. 对每个文件计算 SHA256 → POST `/tasks/:id/offline-submit` 附带 hash
4. 服务端校验 hash，不匹配则要求重传（全量重传，非断点续传）
5. 成功后清理本地缓存

### 7.2 任务异常场景

| 场景 | 系统行为 |
|------|---------|
| 领取后 30 分钟未开始 | 自动释放回待分配池，记异常日志 |
| 领取后 2 小时无更新 | 自动回收 + 通知管理员 |
| 模型调用失败 | 自动降级到备用模型，日志记录降级链路（超时 30s→重试 1 次→fallback） |
| 所有模型都失败 | 任务进死信队列，通知管理员人工处理 |
| 员工本地没装推荐模型 | Agent 检测 → 自动 fallback 到 API 模型 → 任务卡片显示「本地无此模型，将使用 API 版本」 |

### 7.3 并发冲突场景

| 场景 | 措施 |
|------|------|
| 两个员工同时领取同一任务 | Redis 分布式锁，保证一个成功 |
| 自动分配与手动领取冲突 | 同一把分布式锁，后到返回失败 |
| 任务重复提交 | 全局 task_id 去重 + version 字段，结果覆盖不重复计费 |

---

## 八、接口规范与幂等性

以下三个核心 API 必须支持幂等：

| 接口 | 幂等 Key | 说明 |
|------|---------|------|
| `POST /tasks/:id/claim` | `task_id + user_id` | 重复请求不会多次分配 |
| `POST /tasks/:id/submit` | `task_id + version` | 重复提交不会重复扣费 |
| `POST /tasks/:id/progress` | `task_id + progress_seq` | 进度上报幂等 |

**成果提交增加 MD5 校验（Tester 要求）：**

```
POST /tasks/:id/submit

请求体：
{
  "task_id": "uuid",
  "result_url": "minio://...",
  "file_hash": "sha256:xxxx",       ← 客户端计算的 hash
  "output_format": "markdown"       ← 输出格式说明
}

响应：
{
  "status": "ok",
  "message": "成果已提交",
  "file_integrity_verified": true   ← 服务端校验 hash 通过
}
```

所有接口返回值包含 `request_id`，便于追踪。

---

## 九、数据库核心表设计

### 9.1 tasks 表（修正版）

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    department_id TEXT NOT NULL,
    assignee_id TEXT,
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'pending',  -- pending/claimed/processing/completed/failed/dead/suspected
    assignment_strategy TEXT DEFAULT 'manual',  -- manual/auto/hybrid
    recommended_model TEXT,
    override_model TEXT,
    cache_key TEXT,
    result_url TEXT,
    output_format TEXT,              -- 新增：json/markdown/text/image
    created_at TIMESTAMP DEFAULT NOW(),
    claimed_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    claim_timeout_at TIMESTAMP,      -- ✅ 拆分：30 分钟释放点
    inactivity_timeout_at TIMESTAMP, -- ✅ 拆分：2 小时回收点
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    progress_seq INTEGER DEFAULT 0,          -- 进度上报幂等 Key，每次上报+1
    suspected_at TIMESTAMP,          -- 新增：suspected_failure 检测时间
    created_by TEXT,                 -- 新增：创建人
    created_by_role TEXT             -- 新增：创建人角色
);
```

### 9.2 新增：audit_logs 表（Tester 要求）

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action_type TEXT NOT NULL,       -- create_task / claim_task / submit_task / override_model / lock_model / admin_switch
    target_type TEXT NOT NULL,       -- task / model / department / agent
    target_id TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.3 新增：model_registry 表（Backend + Architect 要求）

```sql
CREATE TABLE model_registry (
    id UUID PRIMARY KEY,
    model_name VARCHAR(128) NOT NULL,
    model_type VARCHAR(16) NOT NULL,        -- "local" / "api"
    deploy_location VARCHAR(64),            -- "main" / "dept_A" / "dept_B"
    supported_task_types JSONB NOT NULL,    -- ["代码审查", "文档摘要", ...]
    cost_per_call DECIMAL(10,4),           -- ¥0.03
    avg_latency_ms INTEGER,
    status VARCHAR(16) DEFAULT 'online',    -- online / offline / degraded
    max_pool_size INTEGER,                 -- 并发上限
    min_ram_gb DECIMAL(4,1),               -- 最低内存要求
    version VARCHAR(32),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.4 新增：department_quotas 表

```sql
CREATE TABLE department_quotas (
    id UUID PRIMARY KEY,
    department_id TEXT NOT NULL UNIQUE,
    max_concurrent_tasks INTEGER DEFAULT 10,   -- 计算配额
    max_daily_api_budget DECIMAL(10,2),        -- 费用配额（¥）
    max_daily_upload_mb INTEGER DEFAULT 500,   -- 日上传总量
    max_user_rate INTEGER DEFAULT 5,           -- 用户级软限流阈值
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### 9.5 新增：shared_results 表

```sql
CREATE TABLE shared_results (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id),
    source_department_id TEXT NOT NULL,
    target_department_id TEXT,
    target_user_id TEXT,
    approval_status TEXT DEFAULT 'pending',    -- pending / approved / rejected
    approved_by TEXT,
    file_url TEXT NOT NULL,
    file_hash TEXT,
    output_format TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 十、前端交互设计要点

### 10.1 任务领取 UI

- **待领取任务带呼吸灯提示**，有新任务时浏览器标题闪动 + Notification API 弹窗
- **抢单式领取**：点击后有 0.5s 确认动效（转圈→打勾），给用户「我抢到了」反馈
- **颜色标签**：红色（紧急）、黄色（普通）、灰色（低优先级）
- **模型选择下拉**：
  - 显示可选模型 + 预估耗时/费用对比
  - 管理员锁定时 disabled + tooltip
  - 本地没安装时灰色显示 + 「需下载」
  - 完全没模型时标红提示将使用 API 版本
- **骨架屏**：加载中先 Skeleton 占位

**工作流说明（Frontend 问题）：**
- MVP 模式：员工在 Web 面板领取任务 → 系统提示「任务已分配，请启动本地 Agent 开始处理」
- 员工点「开始处理」→ 任务状态更新为 processing → 前端显示进度条
- 进度上报由 Agent 自动完成，员工不需要手动上报
- 执行完成后成果自动回传

### 10.2 实时更新

- 前端通过 Nginx 反向代理连接 NATS WS（wss://面板域名/ws/nats）
- 订阅 `task.progress.{user_id}` 和 `task.status.{department_id}` topic
- 状态变化实时推送，UI 展示 CI/CD Pipeline 泳道图

### 10.3 移动端

- PWA 方案，管理员手机审批/查进度
- Service Worker 离线通知

### 10.4 完整页面清单 + 导航结构（Frontend 要求）

```
┌─────────────────────────────────────────────────┐
│           OpenCLAW 协作平台                       │
├─────────────────────────────────────────────────┤
│  📋 我的任务             ← 员工默认首页          │
│    ├ 待领取 │ 处理中 │ 已完成                    │
│    ├ 任务列表（卡片式）                            │
│    └ 任务详情（点击展开）                          │
├─────────────────────────────────────────────────┤
│  📂 部门共享库           ← 员工 & 主管           │
│    ├ 列表/网格切换                                │
│    ├ 搜索 + 筛选（按任务类型、时间、格式）        │
│    └ 卡片：标题、部门、输出格式、时间、下载按钮   │
├─────────────────────────────────────────────────┤
│  ⚙️ 管理后台              ← 管理员 & 主管        │
│    ├ 模型配置（model_registry 管理）              │
│    ├ 部门模型锁定（任务类型 × 部门矩阵）          │
│    ├ 配额设置（计算 + 费用 + 用户限流）           │
│    ├ Agent 管理（在线/离线/suspected 列表）       │
│    └ 数据看板（任务、成本、节点大盘）             │
├─────────────────────────────────────────────────┤
│  👤 个人设置              ← 所有人               │
│    ├ 个人资料 + 密码                              │
│    └ Agent 配置（本地模型路径、API Key）          │
└─────────────────────────────────────────────────┘
```

### 10.5 前端 WebSocket 断连策略（Frontend 要求）

| 场景 | 前端行为 |
|------|---------|
| WS 正常 | 实时接收任务状态推送 |
| WS 断连 | 头部显示黄色横幅「连接已断开，显示数据可能有延迟」 |
| WS 断连中 | 任务列表显示上次快照时间，按钮保持可用 |
| WS 重连成功 | 自动刷新全量数据，横幅消失 |
| WS 重连失败（> 30 秒） | 红色横幅「连接异常，请刷新页面」 |

### 10.6 通知机制（Tester 要求）

| 渠道 | MVP | 说明 |
|------|-----|------|
| 浏览器 Notification API | ✅ | 仅当浏览器打开时生效 |
| 浏览器标题闪动 | ✅ | 有新任务时标签页标题闪烁 |
| 站内消息中心 | ✅ | Web 面板右上角铃铛图标；MVP 通知通过 NATS WS topic 实时推送，前端缓存未读计数；V2 再加 `notifications` 表做历史持久化 |
| 邮件通知 | V2 | 任务分配、超时回收时发送 |
| 企业微信/钉钉 | V2 | 第三方推送 |

---

## 十一、开发时间线（15 天 MVP）

| 阶段 | 内容 | 后端 | 前端 | 天数 |
|------|------|------|------|------|
| 第 1-2 天 | 基础框架 + DB 全部表 DDL + JWT + 权限 middleware | 阿强 | 页面框架搭建 | 2 |
| 第 2-3 天 | NATS + JetStream + 认证 + Agent 注册 | 阿强 | — | 2 |
| 第 3-5 天 | 任务 CRUD API + 领取/提交/完成 + 审计日志 | 阿强 | 任务页面 + 领取 UI | 3 |
| 第 5-6 天 | MinIO 集成 + 文件上传（含 MD5）+ 约束 | 阿强 | 成果上传组件 | 2 |
| 第 6-7 天 | 模型路由表 + 三级选择 + fallback 链 | 阿强 | 模型下拉 + 成本对比 | 2 |
| 第 7-8 天 | 进度上报 NATS Pub/Sub + 心跳 Redis + 兜底 | 阿强 | 实时看板 + WS 连接 | 2 |
| 第 8-9 天 | 领取超时 + 自动兜底 + 崩溃检测 | 阿强 | — | 1 |
| 第 9-10 天 | 成果共享 + 共享库 + 管理员后台 API | 阿强 | 共享库 + 管理后台 | 2 |
| **第 10 天** | **搭建独立测试环境（2C4G ¥50/月）** | **全员** | **测试环境** | **1** |
| 第 11-12 天 | 联调 + 灰度部署人事部 | 全员 | 全员 | 2 |
| 第 12-14 天 | 压力测试 + Bug 修复 | 全员 | 全员 | 2 |
| 第 15 天 | 全量上线 | 全员 | 全员 | 1 |
| **总计** | | **13 天** | **10 天** | **15 天** |

---

## 十二、成本测算

### 12.1 固定成本

| 项目 | 月费用 | 说明 |
|------|--------|------|
| 云服务器 4C8G（主节点） | ¥200-300 | 阿里云/腾讯云轻量级 ECS |
| 云服务器 2C4G（测试环境） | ¥50 | 独立测试环境 |
| MinIO 存储 100GB | ¥30 | 对象存储费用 |
| NATS 开源免费 | ¥0 | 开源 |
| 域名 + SSL | ¥20 | 每年 ¥200-300 |
| **合计** | **¥300-400/月** | |

### 12.2 可变成本（模型调用）

| 部门 | 使用模式 | 月预估费用 |
|------|---------|-----------|
| 研发部（10人） | 本地 7B 量化免费 + 深度推理 API 偶发 | ¥0 + ¥30-80 |
| 市场部（5人） | API 文案生成，约 500 次/月 | ¥15-25 |
| 人事部（3人） | 本地小模型 + API 少量 | ¥5-10 |
| **模型月费合计** | | **¥50-115** |

### 12.3 降本测算

| 场景 | 独立部署 | 统一平台 | 节省 |
|------|---------|---------|------|
| 算力 | 每部门各买 GPU | 共享本地模型池 | 60-70% |
| API 调用 | 各买各的 token | 集中采购按量分配 | 30-40% |
| 重复任务 | 无法利用他人结果 | 结果缓存命中 | 20-30% |
| **总降本** | | | **30-50%** |

*注：对比基线为各部门独立部署（GPU 服务器 + 各自买 API token ≈ ¥800-1500/月）。*

---

## 十三、未完成文档清单

| 文档 | 责任人 | 计划时间 |
|------|--------|---------|
| API 详细定义 + 所有表 DDL | 后端阿强 | 开发第 1 天 |
| 前端组件树 + 页面原型 | 前端 | 开发第 1 天 |
| Docker Compose + .env 模板 + healthcheck | Deploy | 开发第 3 天 |
| NATS JetStream 配置（含资源限制）| Deploy | 开发第 2 天 |
| Prometheus 告警规则 + Grafana 大盘 JSON | Deploy | 开发第 7 天 |
| 压力测试方案 | Tester | 开发第 8 天 |
| 灰度上线检查清单 + 回滚 SOP | 全员 | 开发第 10 天 |

---

## 十四、版本记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-05-25 | 初稿 |
| V2.0 | 2026-05-25 | 全员第一轮意见整合 |
| V2.1 | 2026-05-25 | 全员第二轮 46 条意见全部整合 |
| **V2.2** | **2026-05-25** | **全员第三轮 8 条意见全部整合（Reviewer 3 + Backend 4 + PM 1）** |

**审批人：**
- [ ] 高总（项目客户）
- [ ] PM（产品经理）
- [ ] Architect（架构师）
- [ ] Backend（后端）
- [ ] Frontend（前端）
- [ ] Tester（测试）
- [ ] Reviewer（代码守门员）
- [ ] Deploy（运维）
