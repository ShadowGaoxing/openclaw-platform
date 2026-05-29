"""OpenCLAW 分节点 Agent — MVP 版本

PRD V2.2 §6.2:
- NATS 注册 + JWT 验证
- 心跳每 30s 上报 → Redis（fallback 到 HTTP）
- 拉取任务 → 调用模型 → 上传成果（MD5 校验）
- 断网指数退避重连（1s→2s→4s→8s→16s）
- 模型路由配置文件 ~/.openclaw-agent/config.yaml
"""
import asyncio
import hashlib
import json
import logging
import os
import platform
import signal
import socket
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] agent: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent 配置（从环境变量或 config.yaml 读取）"""
    main_node_url: str = os.getenv("OPENCLAW_MAIN_URL", "http://localhost:8000")
    jwt_token: str = os.getenv("OPENCLAW_TOKEN", "")
    agent_name: str = os.getenv("OPENCLAW_AGENT_NAME", f"{socket.gethostname()}-{os.getpid()}")
    department_id: str = os.getenv("OPENCLAW_DEPT_ID", "")
    max_concurrency: int = int(os.getenv("OPENCLAW_MAX_CONC", "2"))
    available_models: List[str] = field(default_factory=lambda: ["qwen2.5-7b", "gpt-4o-mini"])
    heartbeat_interval_s: int = 30
    poll_interval_s: int = 5
    version: str = "0.1.0"


class OpenClawAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.main_node_url,
            timeout=30,
            headers={"Authorization": f"Bearer {config.jwt_token}"} if config.jwt_token else {},
        )
        self.current_concurrency = 0
        self.running = True
        self.registered = False
        self.reconnect_delay = 1  # 指数退避起始

    async def register(self) -> bool:
        """启动时向主节点注册"""
        try:
            res = await self.client.post(
                "/api/v1/agents/register",
                json={
                    "agent_name": self.config.agent_name,
                    "version": self.config.version,
                    "department_id": self.config.department_id,
                    "max_concurrency": self.config.max_concurrency,
                    "available_models": self.config.available_models,
                    "ip_address": socket.gethostbyname(socket.gethostname()),
                },
            )
            res.raise_for_status()
            self.registered = True
            self.reconnect_delay = 1
            logger.info(f"✅ Agent 已注册: {self.config.agent_name}")
            return True
        except Exception as e:
            logger.warning(f"注册失败: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """心跳上报，失败时降级到 fallback"""
        payload = {
            "agent_name": self.config.agent_name,
            "current_concurrency": self.current_concurrency,
            "available_models": self.config.available_models,
        }
        try:
            res = await self.client.post("/api/v1/agents/heartbeat", json=payload)
            if res.status_code == 200:
                return True
        except Exception:
            pass
        # Fallback: PRD §5.3
        try:
            await self.client.get(
                "/api/v1/agents/heartbeat-fallback",
                params={"agent_name": self.config.agent_name},
            )
            logger.info("心跳已 fallback 到 HTTP")
            return True
        except Exception as e:
            logger.warning(f"心跳完全失败: {e}")
            return False

    async def heartbeat_loop(self):
        """周期性心跳"""
        while self.running:
            ok = await self.send_heartbeat()
            if not ok and self.registered:
                # 断网，进入指数退避
                logger.warning(f"心跳失败，{self.reconnect_delay}s 后重连...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 16)
                await self.register()
            else:
                await asyncio.sleep(self.config.heartbeat_interval_s)

    async def poll_tasks(self):
        """轮询拉取任务（MVP 简化版，V1.1 改为 NATS 订阅）"""
        while self.running:
            if self.current_concurrency >= self.config.max_concurrency:
                await asyncio.sleep(self.config.poll_interval_s)
                continue
            try:
                res = await self.client.get(
                    "/api/v1/tasks",
                    params={"status": "assigned_auto", "mine": True, "page_size": 5},
                )
                if res.status_code == 200:
                    body = res.json()
                    items = body.get("data", {}).get("items", [])
                    for task in items:
                        asyncio.create_task(self.process_task(task))
                        if self.current_concurrency >= self.config.max_concurrency:
                            break
            except Exception as e:
                logger.debug(f"拉取任务失败: {e}")
            await asyncio.sleep(self.config.poll_interval_s)

    async def process_task(self, task: dict):
        """执行任务（MVP：mock 处理）"""
        self.current_concurrency += 1
        task_id = task["id"]
        logger.info(f"▶ 开始执行任务 {task_id}: {task.get('title')}")
        try:
            # 1. 标记开始
            await self.client.post(f"/api/v1/tasks/{task_id}/start")

            # 2. 模拟进度上报
            for pct, seq in [(20, 1), (50, 2), (80, 3)]:
                await asyncio.sleep(2)
                try:
                    await self.client.post(
                        f"/api/v1/tasks/{task_id}/progress",
                        json={"progress_seq": seq, "progress_pct": pct, "status_message": f"处理 {pct}%"},
                    )
                except Exception:
                    pass

            # 3. 模拟成果
            result_text = f"# 任务成果 #{task_id[:8]}\n\nMVP 模拟输出"
            result_bytes = result_text.encode()
            file_hash = "sha256:" + hashlib.sha256(result_bytes).hexdigest()

            # 4. 提交（MVP 直接用 file_url 占位）
            await self.client.post(
                f"/api/v1/tasks/{task_id}/submit",
                json={
                    "result_url": f"agent://{self.config.agent_name}/{task_id}/result.md",
                    "file_hash": file_hash,
                    "output_format": "markdown",
                },
            )
            logger.info(f"✓ 任务 {task_id} 已完成")
        except Exception as e:
            logger.error(f"任务 {task_id} 处理失败: {e}")
        finally:
            self.current_concurrency -= 1

    async def run(self):
        """主循环"""
        logger.info(f"🦾 OpenCLAW Agent 启动")
        logger.info(f"  主节点: {self.config.main_node_url}")
        logger.info(f"  Agent 名: {self.config.agent_name}")
        logger.info(f"  部门:   {self.config.department_id}")
        logger.info(f"  并发:   {self.config.max_concurrency}")
        logger.info(f"  模型:   {self.config.available_models}")

        # 注册
        while self.running and not await self.register():
            logger.warning(f"重连等待 {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)
            self.reconnect_delay = min(self.reconnect_delay * 2, 16)

        # 并行运行心跳 + 任务轮询
        await asyncio.gather(
            self.heartbeat_loop(),
            self.poll_tasks(),
        )

    def stop(self):
        self.running = False


async def main():
    config = AgentConfig()
    if not config.jwt_token:
        logger.error("缺少 OPENCLAW_TOKEN 环境变量（需要先登录拿 JWT）")
        sys.exit(1)
    if not config.department_id:
        logger.error("缺少 OPENCLAW_DEPT_ID 环境变量")
        sys.exit(1)

    agent = OpenClawAgent(config)

    def _signal_handler(sig, frame):
        logger.info("收到退出信号，正在停止...")
        agent.stop()

    signal.signal(signal.SIGINT, _signal_handler)
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, _signal_handler)

    try:
        await agent.run()
    finally:
        await agent.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
