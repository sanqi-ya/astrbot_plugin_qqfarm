#!/usr/bin/env python3
"""
AstrBot 插件入口文件
插件名: astrbot_plugin_qqfarm
"""

import asyncio
import logging
from typing import Any

from astrbot.core.star import Star
from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import command
from astrbot.api.message_components import Plain

from .qq_farm_api import QQFarmAPI


class QQFarmPlugin(Star):
    """QQ农场助手插件"""
    
    def __init__(self, context: Any) -> None:
        super().__init__(context)
        self.name = "qqfarm"
        self.api = None
        self._logger = logging.getLogger("qqfarm")
        self._init_api()
    
    def _init_api(self):
        """初始化 API 客户端"""
        config = self.context.get_config()
        base_url = config.get("base_url", "http://103.217.186.84:58130")
        token = config.get("token", "15fe58ac2bc1dc7e4be02621ec72540aa802a36689513ea7")
        
        self.api = QQFarmAPI(
            base_url=base_url,
            token=token
        )
        self._logger.info(f"QQ农场 API 客户端初始化完成，服务器: {base_url}")
    
    @command("农场状态", aliases=["农场", "农场信息", "qq农场"])
    async def farm_status(self, event: AstrMessageEvent):
        """查看农场账号状态"""
        if not self.api:
            yield event.plain_result("❌ API 客户端未初始化")
            return
        
        try:
            accounts = await asyncio.to_thread(self.api.get_accounts)
            if not accounts:
                yield event.plain_result("❌ 未获取到账号列表")
                return
            
            reply = "🍀 QQ农场账号状态\n"
            reply += "-" * 40 + "\n"
            
            for acc in accounts:
                status = "🟢 运行中" if acc.get("running") else "🔴 已停止"
                reply += f"ID: {acc.get('id')} | QQ: {acc.get('qq')} | 昵称: {acc.get('nick')} | 状态: {status}\n"
            
            reply += "-" * 40
            yield event.plain_result(reply)
            
        except Exception as e:
            self._logger.error(f"获取农场状态失败: {e}")
            yield event.plain_result(f"❌ 获取状态失败: {e}")
    
    @command("农场详情", aliases=["农场状态详情"])
    async def farm_detail(self, event: AstrMessageEvent, account_id: str = "1"):
        """查看指定账号的详细状态"""
        if not self.api:
            yield event.plain_result("❌ API 客户端未初始化")
            return
        
        try:
            status = await asyncio.to_thread(self.api.get_status, account_id)
            if not status:
                yield event.plain_result(f"❌ 未获取到账号 {account_id} 的状态")
                return
            
            reply = f"🍀 账号 {account_id} 详情\n"
            reply += "-" * 40 + "\n"
            
            reply += f"昵称: {status.get('status', {}).get('name', '未知')}\n"
            reply += f"等级: {status.get('status', {}).get('level', '未知')}\n"
            reply += f"金币: {status.get('status', {}).get('gold', '未知')}\n"
            reply += f"点券: {status.get('status', {}).get('coupon', '未知')}\n"
            
            uptime = status.get('uptime', 0)
            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)
            reply += f"运行时间: {hours}时{minutes}分{seconds}秒\n"
            
            operations = status.get('operations', {})
            reply += "\n今日操作:\n"
            reply += f"收获: {operations.get('harvest', 0)}\n"
            reply += f"浇水: {operations.get('water', 0)}\n"
            reply += f"除草: {operations.get('weed', 0)}\n"
            reply += f"除虫: {operations.get('bug', 0)}\n"
            reply += f"偷菜: {operations.get('steal', 0)}\n"
            
            reply += "-" * 40
            yield event.plain_result(reply)
            
        except Exception as e:
            self._logger.error(f"获取农场详情失败: {e}")
            yield event.plain_result(f"❌ 获取详情失败: {e}")
    
    @command("更新农场Code", aliases=["农场更新Code", "更新Code"])
    async def farm_update_code(self, event: AstrMessageEvent, account_id: str, code: str):
        """更新农场账号的Code"""
        if not self.api:
            yield event.plain_result("❌ API 客户端未初始化")
            return
        
        try:
            result = await asyncio.to_thread(self.api.update_code, account_id, code)
            if result:
                yield event.plain_result(f"✅ 账号 {account_id} 的 Code 更新成功!")
            else:
                yield event.plain_result(f"❌ 账号 {account_id} 的 Code 更新失败")
                
        except Exception as e:
            self._logger.error(f"更新Code失败: {e}")
            yield event.plain_result(f"❌ 更新失败: {e}")
    
    @command("启动农场", aliases=["农场启动"])
    async def farm_start(self, event: AstrMessageEvent, account_id: str = "1"):
        """启动农场账号"""
        if not self.api:
            yield event.plain_result("❌ API 客户端未初始化")
            return
        
        try:
            result = await asyncio.to_thread(self.api.start_account, account_id)
            if result:
                yield event.plain_result(f"✅ 账号 {account_id} 已启动!")
            else:
                yield event.plain_result(f"❌ 账号 {account_id} 启动失败")
                
        except Exception as e:
            self._logger.error(f"启动账号失败: {e}")
            yield event.plain_result(f"❌ 启动失败: {e}")
    
    @command("停止农场", aliases=["农场停止"])
    async def farm_stop(self, event: AstrMessageEvent, account_id: str = "1"):
        """停止农场账号"""
        if not self.api:
            yield event.plain_result("❌ API 客户端未初始化")
            return
        
        try:
            result = await asyncio.to_thread(self.api.stop_account, account_id)
            if result:
                yield event.plain_result(f"✅ 账号 {account_id} 已停止!")
            else:
                yield event.plain_result(f"❌ 账号 {account_id} 停止失败")
                
        except Exception as e:
            self._logger.error(f"停止账号失败: {e}")
            yield event.plain_result(f"❌ 停止失败: {e}")
    
    @command("农场帮助", aliases=["农场指令"])
    async def farm_help(self, event: AstrMessageEvent):
        """查看农场插件帮助"""
        help_text = "🍀 QQ农场助手指令\n"
        help_text += "-" * 40 + "\n"
        help_text += "🔍 农场状态 - 查看所有账号状态\n"
        help_text += "📊 农场详情 [账号ID] - 查看指定账号详细状态\n"
        help_text += "🔄 更新农场Code [账号ID] [Code] - 更新账号Code\n"
        help_text += "▶️ 启动农场 [账号ID] - 启动农场账号\n"
        help_text += "⏹️ 停止农场 [账号ID] - 停止农场账号\n"
        help_text += "❓ 农场帮助 - 查看此帮助\n"
        help_text += "-" * 40
        yield event.plain_result(help_text)


def get_plugin(context):
    """获取插件实例 - AstrBot 插件入口"""
    return QQFarmPlugin(context)
