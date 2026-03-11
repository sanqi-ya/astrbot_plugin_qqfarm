#!/usr/bin/env python3
"""
AstrBot plugin entry for QQ Farm.
"""

import asyncio
import json
import os
import time
from typing import Optional, Dict, Any, List, Set

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Plain, MessageChain
from astrbot.api.star import Context, Star, register

from .qq_farm_api import QQFarmAPI


@register(
    "astrbot_plugin_qqfarm",
    "sanqi-ya",
    "QQ农场助手插件，通过指令管理QQ农场账号",
    "1.0.0",
    "https://github.com/sanqi-ya/astrbot_plugin_qqfarm",
)
class QQFarmPlugin(Star):
    """QQ农场助手插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.api: Optional[QQFarmAPI] = None

        self._task: Optional[asyncio.Task] = None
        self._state: Dict[str, bool] = {}
        self._last_notify_ts: Dict[str, float] = {}
        self._notify_targets: Set[str] = set()
        self._targets_path = os.path.join(os.path.dirname(__file__), "notify_targets.json")
        self._load_notify_targets()

    async def _init_api_async(self) -> None:
        """Initialize API client from plugin config (async)."""
        config = self.config or {}
        base_url = (config.get("base_url") or "").strip()
        token = (config.get("token") or "").strip()
        admin_password = (config.get("admin_password") or "").strip()

        if not base_url:
            logger.warning("qqfarm: base_url is empty; please configure it in plugin settings.")
            self.api = None
            return

        self.api = QQFarmAPI(
            base_url=base_url,
            token=token,
            admin_password=admin_password,
        )
        await self.api.ainit()
        logger.info(f"qqfarm: API client initialized, server: {base_url}")

        if not self.api.token and self.api.admin_password:
            ok = await self.api.login()
            if ok:
                logger.info("qqfarm: token refreshed via admin password.")
            else:
                logger.warning("qqfarm: failed to refresh token via admin password.")

    async def _get_api(self) -> Optional[QQFarmAPI]:
        if self.api is None:
            await self._init_api_async()
        return self.api

    def _load_notify_targets(self) -> None:
        try:
            if os.path.exists(self._targets_path):
                with open(self._targets_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._notify_targets = set(str(x) for x in data if x)
        except Exception:
            self._notify_targets = set()

    def _save_notify_targets(self) -> None:
        try:
            with open(self._targets_path, "w", encoding="utf-8") as f:
                json.dump(sorted(self._notify_targets), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception(f"qqfarm: failed to save notify targets: {e}")

    def _get_origin_key(self, event: AstrMessageEvent) -> Optional[str]:
        origin = getattr(event, "unified_msg_origin", None)
        if origin is None:
            return None
        return str(origin)

    async def initialize(self):
        """Optional async initialization hook."""
        await self._init_api_async()
        if self._task is None:
            self._task = asyncio.create_task(self._poll_loop())

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._poll_once()
            except Exception as e:
                logger.exception(f"qqfarm: poll loop error: {e}")
            await asyncio.sleep(self._get_interval())

    def _get_interval(self) -> int:
        try:
            return max(10, int((self.config or {}).get("check_interval_sec", 60)))
        except Exception:
            return 60

    def _get_cooldown(self) -> int:
        try:
            return max(0, int((self.config or {}).get("notify_cooldown_sec", 300)))
        except Exception:
            return 300

    async def _poll_once(self) -> None:
        api = await self._get_api()
        if not api:
            return

        accounts = await api.get_accounts()
        if not accounts:
            return

        now = time.time()
        cooldown = self._get_cooldown()

        for acc in accounts:
            acc_id = str(acc.get("id"))
            running = bool(acc.get("running"))

            prev = self._state.get(acc_id)
            self._state[acc_id] = running

            if prev is True and running is False:
                last_ts = self._last_notify_ts.get(acc_id, 0)
                if now - last_ts >= cooldown:
                    await self._notify_offline(acc)
                    self._last_notify_ts[acc_id] = now

    async def _notify_offline(self, acc: Dict[str, Any]) -> None:
        if not self._notify_targets:
            return

        acc_id = acc.get("id")
        qq = acc.get("qq")
        nick = acc.get("nick")
        text = f"⚠️ QQ农场账号掉线：ID={acc_id} QQ={qq} 昵称={nick}"

        for target in list(self._notify_targets):
            try:
                await self.context.send_message(target, MessageChain([Plain(text)]))
            except Exception as e:
                logger.exception(f"qqfarm: failed to notify {target}: {e}")

    @filter.command("农场订阅", aliases=["订阅农场掉线", "农场掉线订阅"])
    async def farm_subscribe(self, event: AstrMessageEvent):
        key = self._get_origin_key(event)
        if not key:
            yield event.plain_result("❌ 无法识别消息来源，订阅失败")
            return

        self._notify_targets.add(key)
        self._save_notify_targets()
        yield event.plain_result("✅ 已订阅农场掉线通知")

    @filter.command("农场退订", aliases=["退订农场掉线", "取消农场订阅"])
    async def farm_unsubscribe(self, event: AstrMessageEvent):
        key = self._get_origin_key(event)
        if not key:
            yield event.plain_result("❌ 无法识别消息来源，退订失败")
            return

        if key in self._notify_targets:
            self._notify_targets.remove(key)
            self._save_notify_targets()
            yield event.plain_result("✅ 已取消农场掉线通知")
        else:
            yield event.plain_result("ℹ️ 当前会话未订阅")

    @filter.command("农场订阅列表", aliases=["农场订阅状态"])
    async def farm_subscribe_list(self, event: AstrMessageEvent):
        count = len(self._notify_targets)
        yield event.plain_result(f"📌 当前订阅数量：{count}")

    @filter.command("农场状态", aliases=["农场", "农场信息", "qq农场"])
    async def farm_status(self, event: AstrMessageEvent):
        """查看农场账号状态"""
        api = await self._get_api()
        if not api:
            yield event.plain_result("❌ 未配置服务器地址，请在插件配置中填写 base_url")
            return

        try:
            accounts = await api.get_accounts()
            if not accounts:
                yield event.plain_result("❌ 未获取到账号列表")
                return

            reply = "🍀 QQ农场账号状态\n"
            reply += "-" * 40 + "\n"

            for acc in accounts:
                status = "🟢 运行中" if acc.get("running") else "🔴 已停止"
                reply += (
                    f"ID: {acc.get('id')} | QQ: {acc.get('qq')} | 昵称: {acc.get('nick')} | 状态: {status}\n"
                )

            reply += "-" * 40
            yield event.plain_result(reply)

        except Exception as e:
            logger.exception(f"获取农场状态失败: {e}")
            yield event.plain_result(f"❌ 获取状态失败: {e}")

    @filter.command("农场详情", aliases=["农场状态详情"])
    async def farm_detail(self, event: AstrMessageEvent, account_id: str = "1"):
        """查看指定账号的详细状态"""
        api = await self._get_api()
        if not api:
            yield event.plain_result("❌ 未配置服务器地址，请在插件配置中填写 base_url")
            return

        try:
            status = await api.get_status(account_id)
            if not status:
                yield event.plain_result(f"❌ 未获取到账号 {account_id} 的状态")
                return

            reply = f"🍀 账号 {account_id} 详情\n"
            reply += "-" * 40 + "\n"

            reply += f"昵称: {status.get('status', {}).get('name', '未知')}\n"
            reply += f"等级: {status.get('status', {}).get('level', '未知')}\n"
            reply += f"金币: {status.get('status', {}).get('gold', '未知')}\n"
            reply += f"点券: {status.get('status', {}).get('coupon', '未知')}\n"

            uptime = status.get("uptime", 0)
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            reply += f"运行时间: {hours}时{minutes}分{seconds}秒\n"

            operations = status.get("operations", {})
            reply += "\n今日操作:\n"
            reply += f"收获: {operations.get('harvest', 0)}\n"
            reply += f"浇水: {operations.get('water', 0)}\n"
            reply += f"除草: {operations.get('weed', 0)}\n"
            reply += f"除虫: {operations.get('bug', 0)}\n"
            reply += f"偷菜: {operations.get('steal', 0)}\n"

            reply += "-" * 40
            yield event.plain_result(reply)

        except Exception as e:
            logger.exception(f"获取农场详情失败: {e}")
            yield event.plain_result(f"❌ 获取详情失败: {e}")

    @filter.command("更新农场Code", aliases=["农场更新Code", "更新Code"])
    async def farm_update_code(self, event: AstrMessageEvent, account_id: str, code: str):
        """更新农场账号的 Code"""
        api = await self._get_api()
        if not api:
            yield event.plain_result("❌ 未配置服务器地址，请在插件配置中填写 base_url")
            return

        try:
            result = await api.update_code(account_id, code)
            if result:
                yield event.plain_result(f"✅ 账号 {account_id} 的 Code 更新成功!")
            else:
                yield event.plain_result(f"❌ 账号 {account_id} 的 Code 更新失败")

        except Exception as e:
            logger.exception(f"更新Code失败: {e}")
            yield event.plain_result(f"❌ 更新失败: {e}")

    @filter.command("启动农场", aliases=["农场启动"])
    async def farm_start(self, event: AstrMessageEvent, account_id: str = "1"):
        """启动农场账号"""
        api = await self._get_api()
        if not api:
            yield event.plain_result("❌ 未配置服务器地址，请在插件配置中填写 base_url")
            return

        try:
            result = await api.start_account(account_id)
            if result:
                yield event.plain_result(f"✅ 账号 {account_id} 已启动!")
            else:
                yield event.plain_result(f"❌ 账号 {account_id} 启动失败")

        except Exception as e:
            logger.exception(f"启动账号失败: {e}")
            yield event.plain_result(f"❌ 启动失败: {e}")

    @filter.command("停止农场", aliases=["农场停止"])
    async def farm_stop(self, event: AstrMessageEvent, account_id: str = "1"):
        """停止农场账号"""
        api = await self._get_api()
        if not api:
            yield event.plain_result("❌ 未配置服务器地址，请在插件配置中填写 base_url")
            return

        try:
            result = await api.stop_account(account_id)
            if result:
                yield event.plain_result(f"✅ 账号 {account_id} 已停止!")
            else:
                yield event.plain_result(f"❌ 账号 {account_id} 停止失败")

        except Exception as e:
            logger.exception(f"停止账号失败: {e}")
            yield event.plain_result(f"❌ 停止失败: {e}")

    @filter.command("农场帮助", aliases=["农场指令"])
    async def farm_help(self, event: AstrMessageEvent):
        """查看农场插件帮助"""
        help_text = "🍀 QQ农场助手指令\n"
        help_text += "-" * 40 + "\n"
        help_text += "🔍 农场状态 - 查看所有账号状态\n"
        help_text += "📊 农场详情 [账号ID] - 查看指定账号详情\n"
        help_text += "🔄 更新农场Code [账号ID] [Code] - 更新账号Code\n"
        help_text += "▶️ 启动农场 [账号ID] - 启动农场账号\n"
        help_text += "⏹️ 停止农场 [账号ID] - 停止农场账号\n"
        help_text += "🛎️ 农场订阅 - 开启掉线通知\n"
        help_text += "🔕 农场退订 - 关闭掉线通知\n"
        help_text += "📌 农场订阅列表 - 查看订阅数量\n"
        help_text += "❓ 农场帮助 - 查看此帮助\n"
        help_text += "-" * 40
        yield event.plain_result(help_text)

    async def terminate(self):
        if self._task:
            self._task.cancel()
            self._task = None
        if self.api:
            await self.api.close()
            self.api = None