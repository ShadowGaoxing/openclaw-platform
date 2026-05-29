"""数据库种子脚本 — 创建默认部门、管理员账号、默认模型

使用方法：
    cd dev/backend
    python -m app.scripts.seed
"""
import asyncio
import logging
from sqlalchemy import select

from app.core.database import AsyncSessionFactory, engine, Base
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.department_quota import DepartmentQuota
from app.models.user import User
from app.models.model_registry import ModelRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed():
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionFactory() as db:
        # ─────── 部门 ───────
        depts_data = [
            {"code": "rd", "name": "研发部"},
            {"code": "market", "name": "市场部"},
            {"code": "hr", "name": "人事部"},
        ]
        dept_id_map = {}
        for d in depts_data:
            result = await db.execute(select(Department).where(Department.code == d["code"]))
            existing = result.scalar_one_or_none()
            if existing:
                dept_id_map[d["code"]] = existing.id
                logger.info(f"部门已存在: {d['name']}")
                continue
            dept = Department(code=d["code"], name=d["name"])
            db.add(dept)
            await db.flush()
            dept_id_map[d["code"]] = dept.id

            # 默认配额
            db.add(DepartmentQuota(department_id=dept.id))
            logger.info(f"创建部门: {d['name']} -> {dept.id}")

        await db.flush()

        # ─────── 用户 ───────
        users_data = [
            {"username": "admin", "password": "admin123", "name": "系统管理员", "role": "admin", "dept": "rd"},
            {"username": "head_rd", "password": "123456", "name": "研发主管", "role": "dept_head", "dept": "rd"},
            {"username": "zhangsan", "password": "123456", "name": "张三", "role": "member", "dept": "rd"},
            {"username": "lisi", "password": "123456", "name": "李四", "role": "member", "dept": "market"},
            {"username": "wangwu", "password": "123456", "name": "王五", "role": "member", "dept": "hr"},
        ]
        for u in users_data:
            result = await db.execute(select(User).where(User.username == u["username"]))
            if result.scalar_one_or_none():
                logger.info(f"用户已存在: {u['username']}")
                continue
            user = User(
                username=u["username"],
                hashed_password=get_password_hash(u["password"]),
                display_name=u["name"],
                department_id=dept_id_map[u["dept"]],
                role=u["role"],
                email=f"{u['username']}@openclaw.local",
            )
            db.add(user)
            logger.info(f"创建用户: {u['username']} (密码: {u['password']})")

        # ─────── 模型注册表 ───────
        models_data = [
            {"name": "qwen2.5-7b", "type": "local", "loc": "main",
             "tasks": ["文档摘要", "翻译", "通用问答"], "cost": 0.0, "lat": 2000, "ram": 4},
            {"name": "deepseek-coder-7b", "type": "local", "loc": "main",
             "tasks": ["代码审查", "代码生成"], "cost": 0.0, "lat": 2500, "ram": 4},
            {"name": "gpt-4o-mini", "type": "api", "loc": None,
             "tasks": ["文案生成", "文档摘要", "通用问答"], "cost": 0.03, "lat": 1500, "ram": None},
            {"name": "doubao", "type": "api", "loc": None,
             "tasks": ["文案生成"], "cost": 0.02, "lat": 1800, "ram": None},
            {"name": "deepseek-r1", "type": "api", "loc": None,
             "tasks": ["深度推理"], "cost": 0.15, "lat": 5000, "ram": None},
            {"name": "sd-xl-turbo", "type": "local", "loc": "main",
             "tasks": ["图像生成"], "cost": 0.0, "lat": 4000, "ram": 6},
        ]
        for m in models_data:
            result = await db.execute(select(ModelRegistry).where(ModelRegistry.model_name == m["name"]))
            if result.scalar_one_or_none():
                logger.info(f"模型已存在: {m['name']}")
                continue
            db.add(ModelRegistry(
                model_name=m["name"],
                model_type=m["type"],
                deploy_location=m["loc"],
                supported_task_types=m["tasks"],
                cost_per_call=m["cost"],
                avg_latency_ms=m["lat"],
                status="online",
                min_ram_gb=m["ram"],
                version="1.0",
            ))
            logger.info(f"注册模型: {m['name']}")

        await db.commit()
        logger.info("✅ 种子数据初始化完成")
        logger.info("登录账号：admin / admin123 (管理员)")
        logger.info("           head_rd / 123456 (研发主管)")
        logger.info("           zhangsan / 123456 (员工)")


if __name__ == "__main__":
    asyncio.run(seed())
