# V2.0 → V2.1 修订对照表

## 参与评审人提出的总问题数：46 条

| 提出人 | 问题数 | 处理状态 |
|-------|--------|---------|
| Reviewer | 8 | ✅ 全部 |
| Frontend | 7 | ✅ 全部 |
| Tester | 8 | ✅ 全部 |
| Deploy | 7 | ✅ 全部 |
| Backend | 6 | ✅ 全部 |
| Architect | 10 | ✅ 全部 |

## 主要结构性变更（20 项）

1. **新增完整权限模型**（Reviewer + Architect）
2. **新增统一审计日志表 `audit_logs`**（Tester）
3. **新增完整 DDL：model_registry / department_quotas / shared_results / audit_logs**（Backend + Architect）
4. **新增前端完整页面清单 + 导航结构**（Frontend）
5. **新增前端 WS 断连策略**（Frontend）
6. **新增 Agent 模型执行器映射表**（Architect）
7. **新增数据隔离粒度定义**（Architect）
8. **新增日志采集方案**（Architect）
9. **新增 Redis 兜底策略**（Deploy）
10. **新增 Prometheus/Grafana 具体方案 + 告警规则**（Deploy）
11. **新增灰度回滚方案**（Deploy）
12. **新增 Agent 自动更新机制（MVP 就做）**（Deploy）
13. **细化灰度方案 + 测试环境预算**（Tester）
14. **细化 fallback 链触发条件**（Backend）
15. **细化离线冲突解决策略**（Tester + Backend）
16. **细化文件上传约束 + MD5 校验**（Deploy + Tester）
17. **细化 V2 路线图**（PM 自查）
18. **新增跨部门共享审批流程**（PM 自查）
19. **新增 Agent 与 OpenCLAW 物理关系图**（PM 自查）
20. **细化深度推理成本**（Reviewer）

## 文件增长

- V2.0：22,599 字节，489 行
- **V2.1：42,640 字节，约 800+ 行**

## 文件位置

`E:/project/openclaw-platform/PRD-V2.1-跨部门OpenCLAW协作系统-终版.md`
