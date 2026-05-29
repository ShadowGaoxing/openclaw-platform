# OpenCLAW 协作平台 V2.2

> 跨部门 AI 任务协作系统 — 主-分节点统一调度，模型按部门按任务类型自动路由最优性价比

## 项目结构

```
openclaw-platform/
├── PRD-V2.1-跨部门OpenCLAW协作系统-终版.md   # 主 PRD（V2.2 内容）
├── docker-compose.yml                       # 全栈编排（生产）
├── .env.example                             # 环境变量模板
├── nginx/nginx.conf                         # Nginx 反向代理 + WS
├── nats/nats-server.conf                    # NATS JetStream 配置
├── monitoring/prometheus.yml                # Prometheus 采集配置
├── dev/
│   ├── backend/                             # FastAPI 后端
│   │   ├── app/
│   │   │   ├── main.py                      # FastAPI 入口
│   │   │   ├── core/                        # config / db / security / redis / nats / minio / scheduler / response
│   │   │   ├── models/                      # 9 张 SQLAlchemy 表
│   │   │   ├── api/                         # 8 个路由模块
│   │   │   └── scripts/seed.py              # 种子数据
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── docker-compose.yml               # 基础设施快速启动（dev）
│   ├── frontend/openclaw-web/               # React + Ant Design Pro
│   │   ├── src/
│   │   │   ├── api/                         # 7 个 API 客户端
│   │   │   ├── pages/                       # Login/TaskList/TaskDetail/SharedLibrary/AdminPanel/Settings
│   │   │   ├── layouts/MainLayout.tsx       # 含 WS 断连横幅
│   │   │   ├── store/                       # zustand 持久化 store
│   │   │   └── types/                       # 共享 TypeScript 类型
│   │   └── vite.config.ts                   # API + WS 代理
│   └── agent/                               # Python 分节点 Agent
│       ├── agent.py                         # 注册/心跳/任务执行
│       ├── config.example.yaml              # 模型路由配置
│       └── requirements.txt
```

## 已实现的功能（按 PRD V2.2 章节）

### §3 关键决策
- ✅ NATS + JetStream（持久化 + WS）
- ✅ 4C8G 部署架构（Docker Compose 资源限制）
- ✅ 手动领取 + 自动兜底分配（Redis 分布式锁 `task:lock:{id}` TTL 10s）
- ✅ 三级模型路由（默认路由 + 员工覆盖 + 管理员锁热推送）

### §5 系统架构
- ✅ Nginx → FastAPI/NATS WS → PG/Redis/MinIO 完整链路
- ✅ 心跳 Redis（TTL 60s）+ HTTP fallback
- ✅ 数据隔离：DB 用 `department_id` + MinIO `bucket/{dept_id}/`
- ✅ 资源限制（每容器 mem_limit）

### §6 功能模块
- ✅ 任务 CRUD + 领取/开始/进度/提交/释放/模型覆盖（幂等）
- ✅ Agent 注册/心跳/列表 + 心跳 fallback
- ✅ 模型注册表 CRUD + NATS 热推送
- ✅ 部门管理 + 配额 + 模型锁定
- ✅ 成果共享 + 跨部门审批
- ✅ 管理员看板 + 审计日志查询
- ✅ 文件上传（MinIO + SHA256 校验 + 50MB 上限 + 类型白名单）

### §6.5 后台调度（每 30/60s）
- ✅ `claim_timeout`：30 分钟未开始 → 释放回 pending
- ✅ `inactivity_timeout`：2 小时无进度 → 自动回收
- ✅ `auto_fallback_assign`：10 分钟无人领 → 分给最低负载 Agent
- ✅ `check_agent_heartbeats`：90s suspected / 120s stale

### §7 错误场景
- ✅ Redis 异常降级到 PG（`/heartbeat-fallback`）
- ✅ 任务幂等（claim → user_id, submit → file_hash, progress → progress_seq）
- ✅ Agent stale 时自动释放其持有任务

### §8 接口规范
- ✅ 统一 `ApiResponse` 包装（status/data/message/request_id/error_code）
- ✅ 三个核心接口幂等

### §9 数据库
- ✅ tasks / users / audit_logs / model_registry / department_quotas / shared_results
- ✅ 新增：agents / departments / department_model_locks

### §10 前端
- ✅ 登录 + 5 个核心页面全部接入真实 API
- ✅ WS 断连横幅（Alert banner）
- ✅ 任务创建/领取/详情/模型选择/进度可视化
- ✅ 共享库 + 搜索筛选
- ✅ 管理后台数据看板 + Agent 列表 + 模型列表
- ✅ 个人设置（profile / password / agent config）

## 快速启动

### 1. 启动基础设施（仅 PG / Redis / NATS / MinIO）

```bash
cd dev/backend
docker compose up -d
```

### 2. 启动后端

```bash
cd dev/backend
pip install -r requirements.txt
python -m app.scripts.seed        # 初始化种子数据
uvicorn app.main:app --reload     # 启动 API
# 访问 http://localhost:8000/docs
```

### 3. 启动前端

```bash
cd dev/frontend/openclaw-web
npm install
npm run dev
# 访问 http://localhost:5173
```

### 4. 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| head_rd | 123456 | 研发主管 |
| zhangsan | 123456 | 研发员工 |

### 5. 启动 Agent（可选）

```bash
cd dev/agent
pip install -r requirements.txt
export OPENCLAW_TOKEN=<从登录拿到 JWT>
export OPENCLAW_DEPT_ID=<部门 UUID>
python agent.py
```

### 6. 全栈部署（生产）

```bash
cp .env.example .env
# 修改 .env 中的密钥
docker compose up -d --build
# 监控套件
docker compose --profile monitoring up -d
```

## 开发者命令

```bash
# 后端
cd dev/backend
python -m py_compile app/**/*.py    # 语法检查

# 前端
cd dev/frontend/openclaw-web
npx tsc --noEmit                    # 类型检查
npm run lint
npm run build
```

## 路线图（V1.1 / V1.2 / V2）

- V1.1：NATS WS 实时推送、Agent 全自动模式、邮件通知、密码修改 API
- V1.2：自动分配算法优化（基于历史成功率）、故障演练、格式转换器
- V2：OpenTelemetry trace、多集群高可用、ELK 集中日志、企业微信集成
