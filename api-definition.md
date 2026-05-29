# OpenCLAW 跨部门协作系统 — REST API 接口定义文档

> **版本**: V1.0  
> **基于**: PRD V2.2 (PM 终审版)  
> **技术栈**: FastAPI + NATS JetStream + PostgreSQL + MinIO + Redis  
> **认证方式**: JWT Bearer Token  
> **日期**: 2026-05-26  
> **状态**: 待开发实现  

---

## 目录

- [通用规范](#通用规范)
- [1. 任务管理 API](#1-任务管理-api)
- [2. 模型管理 API](#2-模型管理-api)
- [3. 部门/配额 API](#3-部门配额-api)
- [4. 成果共享 API](#4-成果共享-api)
- [5. Agent 管理 API](#5-agent-管理-api)
- [6. 审计日志 API](#6-审计日志-api)
- [7. 通知/消息 API](#7-通知消息-api)
- [8. 管理/看板 API](#8-管理看板-api)
- [附录 A: 通用错误码](#附录-a-通用错误码)
- [附录 B: 幂等性说明](#附录-b-幂等性说明)

---

## 通用规范

### 基础 URL

```
https://{panel-domain}/api/v1
```

### 认证方式

所有接口（除健康检查等公开端点外）需要在 HTTP Header 中携带 JWT Bearer Token：

```
Authorization: Bearer <jwt_token>
```

JWT Payload 包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `sub` | string | 用户 ID (user_id) |
| `role` | string | 角色: `admin` / `dept_head` / `member` |
| `department_id` | string | 所属部门 ID |
| `exp` | integer | Token 过期时间戳 (Unix) |

### 统一响应格式

**成功响应**：

```json
{
  "request_id": "uuid-string",
  "data": { ... }
}
```

**分页响应**：

```json
{
  "request_id": "uuid-string",
  "data": {
    "items": [ ... ],
    "total": 42,
    "page": 1,
    "page_size": 20
  }
}
```

**错误响应**：

```json
{
  "request_id": "uuid-string",
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误简述",
    "detail": {"field": "具体错误详情，可包含额外上下文"}
  }
}
```

### 错误码前缀约定

| 范围 | 说明 |
|------|------|
| `4xxx` | 客户端错误 |
| `5xxx` | 服务端错误 |

### 分页参数

| 参数 | 类型 | 默认值 | 最大值 | 说明 |
|------|------|--------|--------|------|
| `page` | integer | 1 | — | 页码，从 1 开始 |
| `page_size` | integer | 20 | 100 | 每页条目数 |

### Content-Type

```
Content-Type: application/json
```

### 日期时间格式

所有时间字段使用 ISO 8601 格式：

```
2026-05-26T10:30:00.000Z
```

### 通用权限要求

| 角色 | 简称 | 权限范围 |
|------|------|----------|
| 系统管理员 | `admin` | 全局读写：模型注册表、所有部门配额、Agent 管理、审计日志、看板 |
| 部门主管 | `dept_head` | 本部门内：任务管理、模型锁定、成果审批、本部门配额查看 |
| 普通员工 | `member` | 个人任务领取/提交、个人成果共享、个人通知 |

> **注**：以下每个接口描述中标注了所需的角色权限。权限校验在 API 层用 middleware 实现，数据层面通过 `WHERE dept_id = current_user.dept_id` 做行级权限隔离。

---

## 1. 任务管理 API

### 1.1 POST /api/v1/tasks — 创建任务

> **权限**: `admin`, `dept_head`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `title` | string | 是 | — | 任务标题，最大 256 字符 |
| `description` | string | 否 | `""` | 任务描述/详细说明 |
| `department_id` | string | 是 | — | 所属部门 ID |
| `priority` | integer | 否 | `3` | 优先级：1(紧急) / 2(高) / 3(普通) / 4(低) |
| `assignment_strategy` | string | 否 | `"manual"` | 分配策略：`manual`(手动领取) / `auto`(自动兜底) / `hybrid`(混合) |
| `recommended_model` | string | 否 | `null` | 推荐模型 ID（不传则由路由自动决定） |
| `created_by` | string | 是 | — | 创建人用户 ID |

**请求示例**：

```json
{
  "title": "研发周报摘要生成",
  "description": "将本周研发周报整理为 500 字以内的摘要",
  "department_id": "dept_rd",
  "priority": 2,
  "assignment_strategy": "hybrid",
  "recommended_model": "qwen2.5-7b",
  "created_by": "user_admin_01"
}
```

**响应 (201 Created)**：

```json
{
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "data": {
    "task_id": "task-uuid-xxxx",
    "status": "pending",
    "created_at": "2026-05-26T10:30:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_CREATE_FAILED` | 创建失败（数据库写入错误等） |
| `DEPARTMENT_NOT_FOUND` | 指定的部门不存在 |
| `INVALID_PRIORITY` | 优先级取值不在 [1-4] 范围内 |
| `INVALID_ASSIGNMENT_STRATEGY` | assignment_strategy 不合法 |

---

### 1.2 GET /api/v1/tasks — 获取任务列表

> **权限**: `admin`, `dept_head`, `member`  
> **数据隔离**: 员工仅看本部门任务，管理员看全局

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `status` | string | 否 | — | 按状态筛选，可多选逗号分隔：`pending,claimed,processing,completed,failed,dead,suspected` |
| `department_id` | string | 否 | — | 按部门筛选（仅管理员可用，非管理员忽略此参数） |
| `assignee_id` | string | 否 | — | 按处理人筛选 |
| `priority` | integer | 否 | — | 按优先级筛选 |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页条目数（最大 100） |
| `sort_by` | string | 否 | `"created_at"` | 排序字段：`created_at`, `priority`, `claimed_at` |
| `sort_order` | string | 否 | `"desc"` | 排序方向：`asc`, `desc` |

**响应 (200 OK)**：

```json
{
  "request_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "data": {
    "items": [
      {
        "id": "task-uuid-xxxx",
        "title": "研发周报摘要生成",
        "description": "将本周研发周报整理为 500 字以内的摘要",
        "status": "pending",
        "department_id": "dept_rd",
        "assignee_id": null,
        "priority": 2,
        "assignment_strategy": "hybrid",
        "recommended_model": "qwen2.5-7b",
        "override_model": null,
        "cache_key": null,
        "result_url": null,
        "output_format": null,
        "created_by": "user_admin_01",
        "created_by_role": "dept_head",
        "created_at": "2026-05-26T10:30:00.000Z",
        "claimed_at": null,
        "started_at": null,
        "completed_at": null,
        "claim_timeout_at": null,
        "inactivity_timeout_at": null,
        "progress_seq": 0
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `INVALID_STATUS_FILTER` | status 参数包含不合法值 |

---

### 1.3 GET /api/v1/tasks/{task_id} — 获取任务详情

> **权限**: `admin`, `dept_head`, `member`（仅限本部门任务或本人领取的任务）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**响应 (200 OK)**：

```json
{
  "request_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "data": {
    "id": "task-uuid-xxxx",
    "title": "研发周报摘要生成",
    "description": "将本周研发周报整理为 500 字以内的摘要",
    "status": "processing",
    "department_id": "dept_rd",
    "assignee_id": "user_zhang_san",
    "priority": 2,
    "assignment_strategy": "hybrid",
    "recommended_model": "qwen2.5-7b",
    "override_model": null,
    "cache_key": null,
    "result_url": null,
    "output_format": "markdown",
    "created_by": "user_admin_01",
    "created_by_role": "dept_head",
    "created_at": "2026-05-26T10:30:00.000Z",
    "claimed_at": "2026-05-26T10:35:00.000Z",
    "started_at": "2026-05-26T10:36:00.000Z",
    "completed_at": null,
    "claim_timeout_at": "2026-05-26T11:05:00.000Z",
    "inactivity_timeout_at": "2026-05-26T12:36:00.000Z",
    "retry_count": 0,
    "max_retries": 3,
    "progress_seq": 5,
    "suspected_at": null
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_ACCESS_DENIED` | 无权限访问此任务 |

---

### 1.4 POST /api/v1/tasks/{task_id}/claim — 领取任务

> **权限**: `member`, `dept_head`  
> **幂等 Key**: `task_id + user_id`  
> **并发控制**: Redis 分布式锁 `task:lock:{task_id}` (TTL = 10s)

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 领取人用户 ID |

**请求示例**：

```json
{
  "user_id": "user_zhang_san"
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "d4e5f6a7-b8c9-0123-defa-123456789abc",
  "data": {
    "status": "claimed",
    "message": "任务领取成功",
    "claimed_at": "2026-05-26T10:35:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_NOT_CLAIMABLE` | 任务当前状态不可领取（非 pending 状态） |
| `TASK_ALREADY_CLAIMED` | 任务已被其他人领取（幂等返回） |
| `TASK_CLAIM_CONFLICT` | 并发冲突，分布式锁争抢失败 |
| `TASK_DEPT_MISMATCH` | 用户所属部门与任务部门不匹配 |
| `QUOTA_EXCEEDED` | 部门当前并发任务数已达上限 |

---

### 1.5 POST /api/v1/tasks/{task_id}/start — 开始处理

> **权限**: `member`, `dept_head`（仅限本人领取的任务）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | 是 | 处理人用户 ID |

**请求示例**：

```json
{
  "user_id": "user_zhang_san"
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "e5f6a7b8-c9d0-1234-efab-23456789abcd",
  "data": {
    "status": "processing",
    "started_at": "2026-05-26T10:36:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_NOT_OWNED` | 此任务不是由当前用户领取的 |
| `TASK_INVALID_STATE` | 任务状态不是 `claimed`，无法开始处理 |
| `TASK_ALREADY_STARTED` | 任务已开始（幂等返回当前状态） |

---

### 1.6 POST /api/v1/tasks/{task_id}/progress — 上报进度

> **权限**: `member`, `dept_head`（仅限本人处理的任务）  
> **幂等 Key**: `task_id + progress_seq`  
> **说明**: 进度上报由本地 Agent 自动完成，员工不需要手动上报。Agent 通过 NATS Pub/Sub 上报，API 层面同时保留此端点作为 fallback。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `progress_seq` | integer | 是 | 进度序列号，每次上报递增 1，作为幂等 Key |
| `progress_pct` | integer | 是 | 进度百分比 (0-100) |
| `status_message` | string | 否 | 当前状态描述，如 "正在加载模型..." |

**请求示例**：

```json
{
  "progress_seq": 3,
  "progress_pct": 60,
  "status_message": "正在生成摘要内容..."
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "f6a7b8c9-d0e1-2345-fabc-34567890abcd",
  "data": {
    "status": "ok",
    "received_seq": 3
  }
}
```

> **幂等响应**：如果重复发送相同的 `progress_seq`，返回与首次相同的响应，不更新 `progress_pct` 和 `status_message`。

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_NOT_ACTIVE` | 任务当前不是 `processing` 状态 |
| `TASK_NOT_OWNED` | 非当前用户处理的任务 |
| `INVALID_PROGRESS_SEQ` | progress_seq 非递增（小于当前已接收的 seq） |
| `INVALID_PROGRESS_PCT` | progress_pct 不在 0-100 范围内 |
| `PROGRESS_SEQ_DUPLICATE` | 重复的 progress_seq，幂等忽略 |

---

### 1.7 POST /api/v1/tasks/{task_id}/submit — 提交成果

> **权限**: `member`, `dept_head`（仅限本人处理的任务）  
> **幂等 Key**: `task_id + version`  
> **说明**: 成果提交包含 MD5 文件校验（Tester 红线要求）。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string (UUID) | 是 | 任务 ID（路径参数与请求体双重校验） |
| `result_url` | string | 是 | 成果文件 URL（MinIO 路径或可下载 URL） |
| `file_hash` | string | 是 | 文件哈希值，格式 `sha256:xxxx`，客户端计算 |
| `output_format` | string | 是 | 输出格式：`json` / `markdown` / `text` / `image` / `csv` / `pdf` |

**请求示例**：

```json
{
  "task_id": "task-uuid-xxxx",
  "result_url": "minio://openclaw/results/task-uuid-xxxx/output.md",
  "file_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "output_format": "markdown"
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "a7b8c9d0-e1f2-3456-abcd-45678901bcde",
  "data": {
    "status": "completed",
    "message": "成果已提交",
    "file_integrity_verified": true
  }
}
```

> `file_integrity_verified = true` 表示服务端成功从 `result_url` 下载文件并校验 hash 匹配。如果校验失败则为 `false`，此时任务状态不变，要求客户端重传。

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_NOT_ACTIVE` | 任务当前不是 `processing` 状态 |
| `TASK_NOT_OWNED` | 非当前用户处理的任务 |
| `INVALID_FILE_HASH` | file_hash 格式不合法（非 `sha256:` 开头） |
| `FILE_INTEGRITY_FAILED` | 服务端下载文件后 hash 校验不匹配 |
| `INVALID_OUTPUT_FORMAT` | output_format 不合法 |
| `FILE_DOWNLOAD_FAILED` | 无法从 result_url 下载文件 |
| `VERSION_CONFLICT` | version 冲突（幂等场景） |

---

### 1.8 POST /api/v1/tasks/{task_id}/offline-submit — 离线提成果交

> **权限**: `member`, `dept_head`  
> **说明**: 离线模式下 Agent 恢复联网后调用。全量提交（不支持断点续传），不校验任务当前状态（允许已超时任务补交）。该接口无幂等 Key 约束，以 `task_id` 唯一去重。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string (UUID) | 是 | 任务 ID |
| `result_url` | string | 是 | 成果文件 URL（本地缓存路径或 MinIO 路径） |
| `file_hash` | string | 是 | 文件 SHA256 哈希 |
| `output_format` | string | 是 | 输出格式 |

**请求示例**：

```json
{
  "task_id": "task-uuid-xxxx",
  "result_url": "file://~/.openclaw-agent/offline-cache/task-uuid-xxxx/output.md",
  "file_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "output_format": "markdown"
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "b8c9d0e1-f2a3-4567-bcde-56789012cdef",
  "data": {
    "status": "completed",
    "file_integrity_verified": true,
    "message": "离线成果已提交"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_ALREADY_COMPLETED` | 任务已完成，重复提交 |
| `FILE_INTEGRITY_FAILED` | hash 校验不匹配，要求全量重传 |
| `FILE_DOWNLOAD_FAILED` | 服务端无法下载文件 |

---

### 1.9 POST /api/v1/tasks/{task_id}/release — 释放任务（超时/异常）

> **权限**: `admin`, `dept_head`, `member`（仅限本人领取的任务）  
> **说明**: 员工主动释放任务（异常退出、放弃处理等），任务回到 `pending` 状态供其他人领取。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string (UUID) | 任务 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reason` | string | 是 | 释放原因说明 |

**请求示例**：

```json
{
  "reason": "本地模型资源不足，无法处理此任务"
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "c9d0e1f2-a3b4-5678-cdef-67890123def0",
  "data": {
    "status": "released",
    "released_at": "2026-05-26T11:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_NOT_CLAIMED` | 任务未被领取，无法释放 |
| `TASK_NOT_OWNED` | 当前用户不是此任务的处理人 |
| `TASK_ALREADY_COMPLETED` | 任务已完成，不可释放 |

---

## 2. 模型管理 API

### 2.1 GET /api/v1/models — 获取模型注册表

> **权限**: `admin`, `dept_head`, `member`  
> **说明**: 返回所有可用的模型列表。部门主管和管理员可查看完整列表，普通员工仅看到本部门可用的模型。

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `task_type` | string | 否 | — | 按任务类型筛选（返回支持此类型的模型） |
| `status` | string | 否 | — | 按状态筛选：`online` / `offline` / `degraded` |
| `model_type` | string | 否 | — | 按模型类型筛选：`local` / `api` |
| `department_id` | string | 否 | — | 按部署部门筛选（仅管理员可用） |

**响应 (200 OK)**：

```json
{
  "request_id": "d0e1f2a3-b4c5-6789-defa-78901234ef01",
  "data": {
    "items": [
      {
        "id": "model-uuid-xxxx",
        "model_name": "qwen2.5-7b",
        "model_type": "local",
        "deploy_location": "main",
        "supported_task_types": ["文档摘要", "文案生成", "代码审查"],
        "cost_per_call": 0.0,
        "avg_latency_ms": 3200,
        "status": "online",
        "max_pool_size": 4,
        "min_ram_gb": 8.0,
        "version": "1.2.0",
        "created_at": "2026-05-20T08:00:00.000Z"
      },
      {
        "id": "model-uuid-yyyy",
        "model_name": "gpt-4o-mini",
        "model_type": "api",
        "deploy_location": "cloud",
        "supported_task_types": ["文案生成", "翻译", "内容总结"],
        "cost_per_call": 0.03,
        "avg_latency_ms": 1500,
        "status": "online",
        "max_pool_size": 20,
        "min_ram_gb": 0.0,
        "version": "latest",
        "created_at": "2026-05-20T08:00:00.000Z"
      }
    ],
    "total": 2
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `INVALID_TASK_TYPE` | task_type 筛选参数不合法 |

---

### 2.2 POST /api/v1/models — 新增/注册模型

> **权限**: `admin`

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `model_name` | string | 是 | — | 模型名称，如 `qwen2.5-7b` |
| `model_type` | string | 是 | — | 模型类型：`local`(本地部署) / `api`(API 调用) |
| `deploy_location` | string | 否 | `"main"` | 部署位置：`main`(主节点) / 部门 ID / `cloud` |
| `supported_task_types` | array[string] | 是 | — | 支持的任务类型列表，如 `["文档摘要", "文案生成"]` |
| `cost_per_call` | number | 是 | — | 单次调用费用（元），本地模型填 `0.0` |
| `avg_latency_ms` | integer | 否 | `0` | 预估平均延迟（毫秒） |
| `max_pool_size` | integer | 否 | `1` | 最大并发数 |
| `min_ram_gb` | number | 否 | `0.0` | 最低内存要求（GB） |
| `version` | string | 否 | `"1.0.0"` | 模型版本号 |

**请求示例**：

```json
{
  "model_name": "deepseek-coder-7b",
  "model_type": "local",
  "deploy_location": "dept_rd",
  "supported_task_types": ["代码审查", "代码生成"],
  "cost_per_call": 0.0,
  "avg_latency_ms": 2800,
  "max_pool_size": 2,
  "min_ram_gb": 8.0,
  "version": "1.0.0"
}
```

**响应 (201 Created)**：

```json
{
  "request_id": "e1f2a3b4-c5d6-7890-efab-89012345f012",
  "data": {
    "id": "model-uuid-new",
    "model_name": "deepseek-coder-7b",
    "status": "online",
    "created_at": "2026-05-26T11:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `MODEL_NAME_EXISTS` | 模型名称已存在 |
| `INVALID_MODEL_TYPE` | model_type 不是 `local` 或 `api` |
| `INVALID_COST` | cost_per_call 为负数 |
| `INVALID_TASK_TYPES` | supported_task_types 为空或包含不合法值 |

---

### 2.3 PUT /api/v1/models/{model_id} — 更新模型配置

> **权限**: `admin`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `model_id` | string (UUID) | 模型 ID |

**请求体**（支持部分更新，仅传入需要修改的字段）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_name` | string | 否 | 模型名称 |
| `model_type` | string | 否 | 模型类型 |
| `deploy_location` | string | 否 | 部署位置 |
| `supported_task_types` | array[string] | 否 | 支持的任务类型 |
| `cost_per_call` | number | 否 | 单次调用费用 |
| `avg_latency_ms` | integer | 否 | 预估平均延迟 |
| `max_pool_size` | integer | 否 | 最大并发数 |
| `min_ram_gb` | number | 否 | 最低内存要求 |
| `version` | string | 否 | 版本号 |
| `status` | string | 否 | 状态：`online` / `offline` / `degraded` |

**请求示例**：

```json
{
  "cost_per_call": 0.02,
  "status": "online",
  "max_pool_size": 8
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "f2a3b4c5-d6e7-8901-fabc-90123456abc1",
  "data": {
    "id": "model-uuid-xxxx",
    "model_name": "qwen2.5-7b",
    "cost_per_call": 0.02,
    "status": "online",
    "max_pool_size": 8,
    "updated_at": "2026-05-26T11:15:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `MODEL_NOT_FOUND` | 模型不存在 |
| `MODEL_NAME_EXISTS` | 修改后的模型名称与其他模型冲突 |

---

### 2.4 DELETE /api/v1/models/{model_id} — 删除模型

> **权限**: `admin`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `model_id` | string (UUID) | 模型 ID |

**响应 (200 OK)**：

```json
{
  "request_id": "a3b4c5d6-e7f8-9012-abcd-01234567bcde",
  "data": {
    "status": "deleted",
    "message": "模型已删除"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `MODEL_NOT_FOUND` | 模型不存在 |
| `MODEL_IN_USE` | 模型正在被使用（有任务依赖此模型），无法删除 |

---

### 2.5 POST /api/v1/models/route — 模型路由决策

> **权限**: `admin`, `dept_head`, `member`  
> **说明**: 根据任务类型、部门和输入特征，自动推荐最优模型。这是后端自动路由的核心接口。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_type` | string | 是 | 任务类型 |
| `department_id` | string | 是 | 部门 ID |
| `input_hash` | string | 否 | 输入内容的 hash（用于缓存结果匹配） |

**请求示例**：

```json
{
  "task_type": "文档摘要",
  "department_id": "dept_market",
  "input_hash": "sha256:abc123..."
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "b4c5d6e7-f8a9-0123-bcde-12345678cdef",
  "data": {
    "recommended_model": {
      "id": "model-uuid-xxxx",
      "model_name": "qwen2.5-7b",
      "cost_per_call": 0.0,
      "deploy_location": "main"
    },
    "fallback_model": {
      "id": "model-uuid-yyyy",
      "model_name": "gpt-4o-mini",
      "cost_per_call": 0.03,
      "deploy_location": "cloud"
    },
    "cost_estimate": 0.0,
    "route_reason": "部门 dept_market 的文档摘要任务，默认路由到最便宜的本地模型 qwen2.5-7b。管理员未锁定模型，输入 hash 无缓存命中。",
    "cache_hit": false
  }
}
```

**路由决策逻辑**：

1. 检查部门管理员锁定的模型（三级锁定），如果有锁定模型则直接返回
2. 检查输入 hash 是否有缓存命中，如果命中返回缓存结果
3. 自动路由默认走成本最低的可用模型
4. 如果首个推荐模型不可用（Agent 未安装/离线），依次尝试 fallback 链
5. 每次路由决策记录到审计日志

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `NO_MODEL_AVAILABLE` | 无可用模型（所有模型离线或无匹配模型） |
| `INVALID_TASK_TYPE` | 不支持的任务类型 |
| `ROUTE_FAILED` | 路由决策失败 |

---

## 3. 部门/配额 API

### 3.1 GET /api/v1/departments/{dept_id}/quotas — 获取部门配额

> **权限**: `admin`, `dept_head`（部门主管仅看本部门）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `dept_id` | string | 部门 ID |

**响应 (200 OK)**：

```json
{
  "request_id": "c5d6e7f8-a9b0-1234-cdef-23456789def0",
  "data": {
    "department_id": "dept_rd",
    "max_concurrent_tasks": 10,
    "max_daily_api_budget": 100.00,
    "max_daily_upload_mb": 500,
    "max_user_rate": 5,
    "current_concurrent_tasks": 3,
    "today_api_spent": 12.50,
    "today_upload_mb": 45,
    "updated_at": "2026-05-26T10:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `DEPARTMENT_NOT_FOUND` | 部门不存在 |
| `ACCESS_DENIED` | 无权限查看此部门配额 |

---

### 3.2 PUT /api/v1/departments/{dept_id}/quotas — 更新部门配额

> **权限**: `admin`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `dept_id` | string | 部门 ID |

**请求体**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `max_concurrent_tasks` | integer | 否 | — | 最大并发任务数（计算配额） |
| `max_daily_api_budget` | number | 否 | — | 日 API 调用预算（元） |
| `max_daily_upload_mb` | integer | 否 | — | 日上传总量上限（MB） |
| `max_user_rate` | integer | 否 | — | 用户级软限流阈值（每分钟请求数） |

**请求示例**：

```json
{
  "max_concurrent_tasks": 15,
  "max_daily_upload_mb": 1000
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "d6e7f8a9-b0c1-2345-defa-34567890ef01",
  "data": {
    "department_id": "dept_rd",
    "max_concurrent_tasks": 15,
    "max_daily_api_budget": 100.00,
    "max_daily_upload_mb": 1000,
    "max_user_rate": 5,
    "updated_at": "2026-05-26T11:30:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `DEPARTMENT_NOT_FOUND` | 部门不存在 |
| `INVALID_QUOTA_VALUE` | 配额值不合法（负数或超出系统上限） |

---

### 3.3 POST /api/v1/departments/{dept_id}/model-lock — 锁定部门模型

> **权限**: `admin`, `dept_head`（仅限本部门）
> **说明**: 部门主管可锁定某些任务类型的模型范围。锁定后新任务默认走锁定模型，已分配但未执行的任务保持原选择不强制重置。配置变更通过 NATS 推送热生效。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `dept_id` | string | 部门 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_type` | string | 是 | 需要锁定的任务类型 |
| `model_id` | string (UUID) | 是 | 锁定的模型 ID |

**请求示例**：

```json
{
  "task_type": "文案生成",
  "model_id": "model-uuid-yyyy"
}
```

**响应 (201 Created)**：

```json
{
  "request_id": "e7f8a9b0-c1d2-3456-efab-45678901f012",
  "data": {
    "department_id": "dept_market",
    "task_type": "文案生成",
    "model_id": "model-uuid-yyyy",
    "model_name": "gpt-4o-mini",
    "status": "locked",
    "created_at": "2026-05-26T12:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `DEPARTMENT_NOT_FOUND` | 部门不存在 |
| `MODEL_NOT_FOUND` | 模型不存在 |
| `LOCK_ALREADY_EXISTS` | 该任务类型已被锁定 |
| `TASK_TYPE_NOT_SUPPORTED` | 模型不支持该任务类型 |

---

### 3.4 DELETE /api/v1/departments/{dept_id}/model-lock — 解除部门模型锁定

> **权限**: `admin`, `dept_head`（仅限本部门）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `dept_id` | string | 部门 ID |

**Query 参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_type` | string | 是 | 需要解除锁定的任务类型 |

**响应 (200 OK)**：

```json
{
  "request_id": "f8a9b0c1-d2e3-4567-fabc-56789012abcd",
  "data": {
    "department_id": "dept_market",
    "task_type": "文案生成",
    "status": "unlocked",
    "message": "模型锁定已解除"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `LOCK_NOT_FOUND` | 未找到该任务类型的锁定记录 |

---

### 3.5 GET /api/v1/departments/{dept_id}/model-locks — 获取部门模型锁定列表

> **权限**: `admin`, `dept_head`（仅限本部门）, `member`（仅查看）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `dept_id` | string | 部门 ID |

**响应 (200 OK)**：

```json
{
  "request_id": "a9b0c1d2-e3f4-5678-abcd-67890123bcde",
  "data": {
    "items": [
      {
        "id": "lock-uuid-xxxx",
        "department_id": "dept_market",
        "task_type": "文案生成",
        "model_id": "model-uuid-yyyy",
        "model_name": "gpt-4o-mini",
        "locked_by": "user_li_si",
        "created_at": "2026-05-26T12:00:00.000Z"
      }
    ],
    "total": 1
  }
}
```

---

## 4. 成果共享 API

### 4.1 POST /api/v1/shared-results — 分享成果

> **权限**: `member`, `dept_head`, `admin`

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string (UUID) | 是 | 来源任务 ID |
| `source_department_id` | string | 是 | 来源部门 ID |
| `target_department_id` | string | 否 | 目标部门 ID（与 target_user_id 二选一） |
| `target_user_id` | string | 否 | 目标用户 ID（与 target_department_id 二选一） |
| `file_url` | string | 是 | 成果文件 URL |

**请求示例**：

```json
{
  "task_id": "task-uuid-xxxx",
  "source_department_id": "dept_rd",
  "target_department_id": "dept_market",
  "file_url": "minio://openclaw/shared/task-uuid-xxxx/output.md"
}
```

**响应 (201 Created)**：

```json
{
  "request_id": "b0c1d2e3-f4a5-6789-bcde-78901234cdef",
  "data": {
    "id": "shared-uuid-xxxx",
    "status": "pending",
    "message": "分享请求已提交，等待目标部门审批",
    "created_at": "2026-05-26T13:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_NOT_COMPLETED` | 任务未完成无法分享 |
| `SHARE_TARGET_REQUIRED` | 需要指定 target_department_id 或 target_user_id 其中之一 |
| `FILE_NOT_FOUND` | 成果文件不存在 |

---

### 4.2 GET /api/v1/shared-results — 获取共享成果列表

> **权限**: `admin`, `dept_head`, `member`
> **数据隔离**: 员工仅看到与自己部门相关的共享记录

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `department_id` | string | 否 | — | 按部门筛选（管理员可看任意部门） |
| `status` | string | 否 | — | 筛选：`pending` / `approved` / `rejected` |
| `direction` | string | 否 | — | 方向：`incoming`(收到的) / `outgoing`(发出的) |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页条目数 |

**响应 (200 OK)**：

```json
{
  "request_id": "c1d2e3f4-a5b6-7890-cdef-89012345def0",
  "data": {
    "items": [
      {
        "id": "shared-uuid-xxxx",
        "task_id": "task-uuid-xxxx",
        "task_title": "研发周报摘要生成",
        "source_department_id": "dept_rd",
        "target_department_id": "dept_market",
        "target_user_id": null,
        "approval_status": "pending",
        "approved_by": null,
        "file_url": "minio://openclaw/shared/task-uuid-xxxx/output.md",
        "file_hash": "sha256:e3b0c44...",
        "output_format": "markdown",
        "created_at": "2026-05-26T13:00:00.000Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 4.3 PUT /api/v1/shared-results/{id}/approve — 审批共享成果

> **权限**: `admin`, `dept_head`（仅审批本部门的共享请求）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 共享记录 ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `approved` | boolean | 是 | `true`(批准) / `false`(拒绝) |
| `approved_by` | string | 是 | 审批人用户 ID |
| `comment` | string | 否 | 审批意见 |

**请求示例**：

```json
{
  "approved": true,
  "approved_by": "user_li_si",
  "comment": "这份摘要对市场部很有价值，批准共享"
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "d2e3f4a5-b6c7-8901-defa-90123456ef01",
  "data": {
    "id": "shared-uuid-xxxx",
    "approval_status": "approved",
    "approved_by": "user_li_si",
    "approved_at": "2026-05-26T14:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `SHARED_RESULT_NOT_FOUND` | 共享记录不存在 |
| `SHARED_RESULT_ALREADY_APPROVED` | 已审批，不可重复操作 |
| `ACCESS_DENIED` | 无权审批此共享请求 |

---

### 4.4 GET /api/v1/shared-results/{id}/download — 下载共享成果

> **权限**: `admin`, `dept_head`, `member`（仅限已批准的共享记录且用户有权限）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 共享记录 ID |

**响应 (200 OK)**：

直接返回文件流，HTTP 响应头包含：

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="output.md"
Content-Length: 12345
X-File-Hash: sha256:e3b0c44...
```

**JSON 响应体（当 `Accept: application/json` 时）**：

```json
{
  "request_id": "e3f4a5b6-c7d8-9012-efab-01234567abcd",
  "data": {
    "download_url": "https://minio.openclaw.internal/shared/xxx/output.md?token=xxx",
    "file_name": "output.md",
    "file_size": 12345,
    "file_hash": "sha256:e3b0c44...",
    "expires_in": 3600
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `SHARED_RESULT_NOT_FOUND` | 共享记录不存在 |
| `SHARED_RESULT_NOT_APPROVED` | 尚未批准，不可下载 |
| `ACCESS_DENIED` | 无下载权限 |
| `FILE_NOT_FOUND` | 文件已被删除或不可用 |

---

## 5. Agent 管理 API

### 5.1 GET /api/v1/agents — 获取 Agent 列表

> **权限**: `admin`, `dept_head`（仅看本部门）

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `department_id` | string | 否 | — | 按部门筛选 |
| `status` | string | 否 | — | 按状态筛选：`online` / `offline` / `suspected` |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页条目数 |

**响应 (200 OK)**：

```json
{
  "request_id": "f4a5b6c7-d8e9-0123-fabc-12345678bcde",
  "data": {
    "items": [
      {
        "id": "agent-uuid-xxxx",
        "name": "研发部-张三的机器",
        "department_id": "dept_rd",
        "status": "online",
        "last_heartbeat": "2026-05-26T14:30:00.000Z",
        "current_concurrency": 2,
        "max_concurrency": 4,
        "cpu_usage": 45.2,
        "memory_usage": 6.8,
        "model_list": ["qwen2.5-7b", "deepseek-coder-7b"],
        "ip_address": "192.168.1.100",
        "version": "1.0.0"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 5.2 GET /api/v1/agents/{agent_id} — Agent 详情

> **权限**: `admin`, `dept_head`（仅本部门）, `member`（仅本人）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | string (UUID) | Agent ID |

**响应 (200 OK)**：

```json
{
  "request_id": "a5b6c7d8-e9f0-1234-abcd-23456789cdef",
  "data": {
    "id": "agent-uuid-xxxx",
    "name": "研发部-张三的机器",
    "department_id": "dept_rd",
    "user_id": "user_zhang_san",
    "status": "online",
    "last_heartbeat": "2026-05-26T14:30:00.000Z",
    "current_concurrency": 2,
    "max_concurrency": 4,
    "cpu_usage": 45.2,
    "memory_usage": 6.8,
    "model_list": ["qwen2.5-7b", "deepseek-coder-7b"],
    "local_model_path": "/home/user/.openclaw/models/",
    "ip_address": "192.168.1.100",
    "version": "1.0.0",
    "os_info": "Windows 10 / Ubuntu 22.04",
    "gpu_info": "NVIDIA RTX 3060 12GB",
    "created_at": "2026-05-22T08:00:00.000Z",
    "total_tasks_completed": 47,
    "total_tasks_failed": 2
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `AGENT_NOT_FOUND` | Agent 不存在 |
| `ACCESS_DENIED` | 无权限 |

---

### 5.3 POST /api/v1/agents/{agent_id}/config — 更新 Agent 配置

> **权限**: `admin`, `member`（仅本人）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | string (UUID) | Agent ID |

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `local_model_path` | string | 否 | 本地模型路径 |
| `max_concurrency` | integer | 否 | 最大并发数 |
| `model_list` | array[string] | 否 | 本地已安装的模型列表 |
| `api_key_config` | object | 否 | API Key 配置（敏感信息，不返回给前端） |

**请求示例**：

```json
{
  "max_concurrency": 6,
  "local_model_path": "/home/user/.openclaw/models/",
  "model_list": ["qwen2.5-7b", "deepseek-coder-7b", "llama3-8b"]
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "b6c7d8e9-f0a1-2345-bcde-34567890def0",
  "data": {
    "agent_id": "agent-uuid-xxxx",
    "status": "configured",
    "updated_at": "2026-05-26T15:00:00.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `AGENT_NOT_FOUND` | Agent 不存在 |
| `ACCESS_DENIED` | 无权限修改此 Agent 配置 |

---

### 5.4 POST /api/v1/agents/heartbeat — Agent 心跳上报

> **权限**: Agent 内部调用（通过 NATS JWT 认证或 JWT Token）
> **说明**: Agent 定期（默认每 15 秒）上报状态。连续 3 次 Redis 写入失败时降级为直接 POST 到此 API 写入 PG。

**请求体**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string (UUID) | 是 | Agent ID |
| `department_id` | string | 是 | 所属部门 ID |
| `status` | string | 是 | 状态：`online` / `offline` / `busy` |
| `current_concurrency` | integer | 是 | 当前并发任务数 |
| `max_concurrency` | integer | 是 | 最大并发数 |
| `cpu_usage` | number | 否 | CPU 使用率 (%) |
| `memory_usage` | number | 否 | 内存使用量 (GB) |
| `model_list` | array[string] | 否 | 本地可用模型列表 |
| `gpu_usage` | number | 否 | GPU 使用率 (%)（如果有 GPU） |

**请求示例**：

```json
{
  "agent_id": "agent-uuid-xxxx",
  "department_id": "dept_rd",
  "status": "online",
  "current_concurrency": 2,
  "max_concurrency": 4,
  "cpu_usage": 45.2,
  "memory_usage": 6.8,
  "model_list": ["qwen2.5-7b", "deepseek-coder-7b"],
  "gpu_usage": 32.5
}
```

**响应 (200 OK)**：

```json
{
  "request_id": "c7d8e9f0-a1b2-3456-cdef-45678901ef01",
  "data": {
    "status": "ack",
    "received_at": "2026-05-26T14:30:15.000Z"
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `AGENT_NOT_FOUND` | Agent 未注册，需要先注册 |
| `INVALID_HEARTBEAT_DATA` | 心跳数据不合法 |

---

## 6. 审计日志 API

### 6.1 GET /api/v1/audit-logs — 获取审计日志

> **权限**: `admin`, `dept_head`（仅看本部门相关）

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `actor_id` | string | 否 | — | 按操作人筛选 |
| `actor_role` | string | 否 | — | 按角色筛选：`admin` / `dept_head` / `member` |
| `action_type` | string | 否 | — | 操作类型：`create_task` / `claim_task` / `start_task` / `submit_task` / `release_task` / `override_model` / `lock_model` / `unlock_model` / `admin_switch` / `share_result` / `approve_share` / `route_decision` |
| `target_type` | string | 否 | — | 目标类型：`task` / `model` / `department` / `agent` / `shared_result` |
| `target_id` | string | 否 | — | 目标对象 ID |
| `department_id` | string | 否 | — | 按部门筛选 |
| `start_time` | string (ISO 8601) | 否 | — | 筛选开始时间 |
| `end_time` | string (ISO 8601) | 否 | — | 筛选结束时间 |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页条目数（最大 100） |
| `sort_order` | string | 否 | `"desc"` | 排序方向 |

**响应 (200 OK)**：

```json
{
  "request_id": "d8e9f0a1-b2c3-4567-defa-56789012abcd",
  "data": {
    "items": [
      {
        "id": 10042,
        "actor_id": "user_zhang_san",
        "actor_role": "member",
        "action_type": "claim_task",
        "target_type": "task",
        "target_id": "task-uuid-xxxx",
        "old_value": null,
        "new_value": {
          "status": "claimed",
          "assignee_id": "user_zhang_san"
        },
        "department_id": "dept_rd",
        "ip_address": "192.168.1.100",
        "user_agent": "OpenCLAW-Agent/1.0.0",
        "created_at": "2026-05-26T10:35:00.000Z"
      }
    ],
    "total": 1245,
    "page": 1,
    "page_size": 20
  }
}
```

**错误码**：

| 错误码 | 说明 |
|--------|------|
| `INVALID_DATE_RANGE` | 时间范围不合法（start_time 大于 end_time） |
| `INVALID_ACTION_TYPE` | action_type 不合法 |

---

## 7. 通知/消息 API

> **说明**: MVP 阶段通知通过 NATS WS topic 实时推送，Web 面板右上角铃铛图标显示未读计数，前端缓存未读计数。V2 再加 `notifications` 表做历史持久化。以下 API 为 V2 预留接口，MVP 中 `/api/v1/notifications` 返回的内容从前端本地缓存读取。

### 7.1 GET /api/v1/notifications — 获取通知列表

> **权限**: `admin`, `dept_head`, `member`（仅看本人通知）  
> **状态**: V2 实现

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `unread_only` | boolean | 否 | `false` | 仅返回未读通知 |
| `type` | string | 否 | — | 通知类型：`task_assigned` / `task_expired` / `share_request` / `share_approved` / `model_fallback` / `system_alert` |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页条目数 |

**响应 (200 OK)**：

```json
{
  "request_id": "e9f0a1b2-c3d4-5678-efab-67890123bcde",
  "data": {
    "items": [
      {
        "id": "notif-uuid-xxxx",
        "type": "task_assigned",
        "title": "您有新任务",
        "message": "任务「研发周报摘要生成」已分配给您，请尽快处理",
        "task_id": "task-uuid-xxxx",
        "is_read": false,
        "created_at": "2026-05-26T10:35:00.000Z"
      }
    ],
    "total": 15,
    "unread_count": 3,
    "page": 1,
    "page_size": 20
  }
}
```

### 7.2 PUT /api/v1/notifications/{id}/read — 标记已读

> **权限**: `admin`, `dept_head`, `member`（仅本人通知）

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 通知 ID |

**响应 (200 OK)**：

```json
{
  "request_id": "f0a1b2c3-d4e5-6789-fabc-78901234cdef",
  "data": {
    "id": "notif-uuid-xxxx",
    "is_read": true,
    "read_at": "2026-05-26T15:30:00.000Z"
  }
}
```

### 7.3 PUT /api/v1/notifications/read-all — 全部标记已读

> **权限**: `admin`, `dept_head`, `member`（仅本人通知）

**响应 (200 OK)**：

```json
{
  "request_id": "a1b2c3d4-e5f6-7890-abcd-89012345def0",
  "data": {
    "status": "ok",
    "updated_count": 5,
    "message": "所有通知已标记为已读"
  }
}
```

---

## 8. 管理/看板 API

### 8.1 GET /api/v1/dashboard/task-stats — 任务统计数据

> **权限**: `admin`, `dept_head`（仅看本部门）

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `department_id` | string | 否 | — | 按部门筛选（管理员可用） |
| `start_time` | string (ISO 8601) | 否 | 当天 00:00 | 统计起始时间 |
| `end_time` | string (ISO 8601) | 否 | 当前时间 | 统计结束时间 |

**响应 (200 OK)**：

```json
{
  "request_id": "b2c3d4e5-f6a7-8901-bcde-90123456ef01",
  "data": {
    "period": {
      "start_time": "2026-05-26T00:00:00.000Z",
      "end_time": "2026-05-26T16:00:00.000Z"
    },
    "summary": {
      "pending": 12,
      "claimed": 3,
      "processing": 5,
      "completed": 28,
      "failed": 2,
      "dead": 0,
      "suspected": 1,
      "total": 51
    },
    "by_department": {
      "dept_rd": {
        "pending": 5,
        "processing": 2,
        "completed": 15,
        "failed": 1
      },
      "dept_market": {
        "pending": 4,
        "processing": 2,
        "completed": 8,
        "failed": 1
      },
      "dept_hr": {
        "pending": 3,
        "processing": 1,
        "completed": 5,
        "failed": 0
      }
    },
    "by_priority": {
      "1": {"pending": 2, "completed": 5},
      "2": {"pending": 4, "completed": 10},
      "3": {"pending": 4, "completed": 10},
      "4": {"pending": 2, "completed": 3}
    }
  }
}
```

---

### 8.2 GET /api/v1/dashboard/cost-stats — 成本统计数据

> **权限**: `admin`, `dept_head`（仅看本部门）

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `department_id` | string | 否 | — | 按部门筛选 |
| `start_time` | string (ISO 8601) | 否 | 当天 00:00 | 统计起始时间 |
| `end_time` | string (ISO 8601) | 否 | 当前时间 | 统计结束时间 |

**响应 (200 OK)**：

```json
{
  "request_id": "c3d4e5f6-a7b8-9012-cdef-01234567abcd",
  "data": {
    "period": {
      "start_time": "2026-05-26T00:00:00.000Z",
      "end_time": "2026-05-26T16:00:00.000Z"
    },
    "daily_cost": 12.50,
    "monthly_cost": 245.80,
    "by_department": {
      "dept_rd": {
        "daily_cost": 5.20,
        "monthly_cost": 85.50,
        "api_calls": 35,
        "local_executions": 120
      },
      "dept_market": {
        "daily_cost": 6.10,
        "monthly_cost": 120.30,
        "api_calls": 48,
        "local_executions": 15
      },
      "dept_hr": {
        "daily_cost": 1.20,
        "monthly_cost": 40.00,
        "api_calls": 8,
        "local_executions": 25
      }
    },
    "by_model": {
      "qwen2.5-7b": {
        "total_cost": 0.0,
        "total_calls": 85
      },
      "gpt-4o-mini": {
        "total_cost": 10.80,
        "total_calls": 360
      },
      "deepseek-r1": {
        "total_cost": 1.70,
        "total_calls": 11
      }
    }
  }
}
```

---

### 8.3 GET /api/v1/dashboard/agent-status — Agent 状态汇总

> **权限**: `admin`, `dept_head`（仅看本部门）

**Query 参数**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `department_id` | string | 否 | — | 按部门筛选 |

**响应 (200 OK)**：

```json
{
  "request_id": "d4e5f6a7-b8c9-0123-defa-12345678bcde",
  "data": {
    "summary": {
      "total": 15,
      "online": 12,
      "offline": 2,
      "suspected": 1
    },
    "by_department": {
      "dept_rd": {
        "total": 6,
        "online": 5,
        "offline": 1,
        "suspected": 0,
        "avg_cpu_usage": 38.5,
        "avg_memory_usage": 5.2,
        "total_concurrency": 12,
        "used_concurrency": 5
      },
      "dept_market": {
        "total": 5,
        "online": 4,
        "offline": 0,
        "suspected": 1,
        "avg_cpu_usage": 22.3,
        "avg_memory_usage": 3.1,
        "total_concurrency": 10,
        "used_concurrency": 4
      },
      "dept_hr": {
        "total": 4,
        "online": 3,
        "offline": 1,
        "suspected": 0,
        "avg_cpu_usage": 15.8,
        "avg_memory_usage": 2.5,
        "total_concurrency": 8,
        "used_concurrency": 2
      }
    }
  }
}
```

---

## 附录 A: 通用错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `UNAUTHORIZED` | 401 | 未认证或 Token 失效 |
| `FORBIDDEN` | 403 | 无权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | HTTP 方法不允许 |
| `VALIDATION_ERROR` | 422 | 请求体校验失败 |
| `RATE_LIMITED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务暂不可用 |
| `REQUEST_TIMEOUT` | 504 | 上游请求超时 |
| `DEPARTMENT_NOT_FOUND` | 404 | 部门不存在 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `MODEL_NOT_FOUND` | 404 | 模型不存在 |
| `AGENT_NOT_FOUND` | 404 | Agent 不存在 |
| `QUOTA_EXCEEDED` | 429 | 配额超限 |

### 错误响应体示例

```json
{
  "request_id": "req-uuid-xxxx",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数校验失败",
    "detail": {
      "title": ["字段不能为空"],
      "department_id": ["字段不能为空"]
    }
  }
}
```

```json
{
  "request_id": "req-uuid-xxxx",
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "部门并发任务数已达上限",
    "detail": {
      "limit": 10,
      "current": 10,
      "quota_type": "max_concurrent_tasks"
    }
  }
}
```

---

## 附录 B: 幂等性说明

根据 PRD V2.2（Tester 红线要求），以下三个核心 API 必须支持幂等：

| 接口 | 幂等 Key | 实现方式 | 说明 |
|------|---------|---------|------|
| `POST /api/v1/tasks/{task_id}/claim` | `task_id + user_id` | Redis 分布式锁 + 数据库唯一约束 | 重复请求不会多次分配，后到返回「任务已被领取」 |
| `POST /api/v1/tasks/{task_id}/submit` | `task_id + version` | 数据库唯一约束 (task_id, version) | 重复提交不会重复扣费，结果覆盖不重复计费 |
| `POST /api/v1/tasks/{task_id}/progress` | `task_id + progress_seq` | 数据库唯一约束 (task_id, progress_seq) | 重复上报返回相同响应，不更新进度 |

### 幂等性实现方案

1. **Claim 接口**：
   - 使用 Redis 分布式锁 `task:lock:{task_id}` (TTL = 10s) 确保并发安全
   - 锁内检查任务状态是否为 `pending`
   - 更新数据库状态为 `claimed`，设置 `assignee_id` 和 `claim_timeout_at`
   - 重复请求：锁内查到状态非 `pending` 直接返回「已领取」

2. **Submit 接口**：
   - 使用 `(task_id, version)` 做唯一索引
   - 首次提交：插入记录，更新任务状态为 `completed`
   - 重复提交：插入冲突，返回首次提交的响应

3. **Progress 接口**：
   - 使用 `(task_id, progress_seq)` 做唯一索引
   - 首次上报：插入记录，更新 `progress_pct`
   - 重复上报：数据库冲突，返回已接受的 `received_seq`

---

## 附录 C: NATS 主题约定（参考）

以下为 API 文档补充，用于说明实时推送场景的消息主题命名规则：

| 主题 | 说明 | 推送方向 |
|------|------|---------|
| `task.progress.{user_id}` | 进度推送 — 通知特定用户其任务进度更新 | NATS → 前端 WS |
| `task.status.{department_id}` | 状态推送 — 通知某部门所有任务状态变更 | NATS → 前端 WS |
| `agent.heartbeat.{department_id}` | Agent 心跳 — 部门内 Agent 心跳实时汇总 | Agent → NATS |
| `agent.command.{agent_id}` | Agent 指令 — 服务端向特定 Agent 下发指令 | NATS → Agent |
| `model.route.update.{department_id}` | 模型路由热更新 — 管理员修改锁定后推送 | 后端 → NATS |

> **WS 连接**: 前端通过 `wss://{panel-domain}/ws/nats/` 连接 NATS WebSocket（经 Nginx 反向代理），`proxy_read_timeout 60s`。
>
> **断连策略**:
> - 断连时头部显示黄色横幅「连接已断开，显示数据可能有延迟」
> - > 30 秒重连失败 → 红色横幅「连接异常，请刷新页面」
> - 重连成功 → 自动刷新全量数据

---

> **文档结尾** — OpenCLAW API Definition V1.0  
> 基于 PRD V2.2 (PM 终审版)  
> 如发现不一致之处，以 PRD V2.2 为准。
