# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/11/19 20:09
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : __init__.py.py
# @Software: PyCharm
import json

from nonebot import on_command, logger, get_driver
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.exception import FinishedException, RejectedException
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment, Event, GroupMessageEvent, PrivateMessageEvent
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import ArgStr, ArgPlainText
from nonebot.params import CommandArg
from nonebot.typing import T_State

from . import utils, path, user_agent
from .path import *
from .utils import *
from .utils_net import *

driver = get_driver()
global_config = driver.config
try:
    account = str(global_config.youth_account)
    password = str(global_config.youth_password)
    youth_num = str(global_config.youth_number)
    youth_group = global_config.youth_group
except AttributeError:
    logger.warning("未配置青年大学习插件，请根据README.md配置")
    account = None
    password = None
    youth_num = None
    youth_group = None


@driver.on_bot_connect
async def _():
    await utils.plugin_init()


youth_checker = on_command("查大学习", aliases={"查询大学习", "提醒大学习"}, priority=2, block=True)


@youth_checker.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, matcher: Matcher, args: Message = CommandArg()):
    lock_r = "一个查询正在进行，请稍后再试\n"
    if LOCK_PATH.exists():
        if isinstance(event, GroupMessageEvent):
            lock_r += MessageSegment.at(event.user_id)
        await youth_checker.finish(lock_r)
    else:
        LOCK_PATH.touch()
    await youth_checker.send("请稍后...")
    state["mode"] = "normal"
    if isinstance(event, GroupMessageEvent):
        if event.group_id not in youth_group:
            await unlock()
            await youth_checker.finish("本群不在配置的群列表中，无法使用此功能")
    if args:
        if str(args).replace(" ", "") == "@":
            if isinstance(event, GroupMessageEvent):
                state["mode"] = "at"
                await youth_checker.send(
                    "本次操作将 @ 未学习的支部成员\n请确保\n /陕西共青团工具\n 文件夹下有 姓名-QQ 对应的 excel 文件")
            else:
                await youth_checker.send("私聊中不支持 @ 模式，将使用正常模式")

    if "verify" not in state:
        bowser = await playwright_login()
        context = bowser[0]
        page = bowser[1]
        if isinstance(context, utils_net.BrowserContext):
            await youth_checker.send(MessageSegment.image((VERIFY_PATH / "verify.jpg").resolve()))
            state["page"] = page
            state["context"] = context
    else:
        await get_main_cookies(state["context"], state["page"], state["verify"])


@youth_checker.got("verify", prompt="请输入验证码\n没收到验证码请回复问号【？】")
async def _(
        event: Event,
        state: T_State,
        verify: str = ArgStr("verify")
):
    try:
        if verify in ["取消", "算了", "退出"]:
            await youth_checker.finish("已取消")
        if verify in ["?", "？", "验证码呢"]:
            await youth_checker.reject(MessageSegment.image((VERIFY_PATH / "verify.jpg").resolve()))
        if len(verify) != 4:
            await youth_checker.reject("验证码长度不正确，请重新输入")
        else:
            state["verify"] = verify
            if not account:
                await youth_checker.finish("未配置青年大学习管理员账号密码，正在退出...")
            try:
                token = await get_main_cookies(
                    context=state["context"],
                    page=state["page"],
                    account=account,
                    password=password,
                    verify=state["verify"])
            except OperationTimedOutError:
                await unlock()
                await youth_checker.finish("登录超时，可能是验证码输入错误，重试请发送 “查大学习” ")
                token = None
            if not token:
                await unlock()
                await youth_checker.finish("登录失败，请重试")
            else:
                headers = {
                    "token": token,
                    "user-agent": str(user_agent.get_user_agent())
                }
                oid = (await httpx_get(
                    # url="https://www.sxgqt.org.cn/bgsxapiv2/organization/getOrganizeMess",
                    url="https://api.sxgqt.org.cn/bgsxapiv2/organization/getOrganizeMess",
                    headers=headers
                )).json()['data']['id']
                OID_PATH.write_text(str(oid))
                params = {
                    'page': '1',
                    'rows': youth_num,
                    'keyword': '',
                    'oid': oid,
                    'leagueStatus': '',
                    'goHomeStatus': '',
                    'memberCardStatus': '',
                    'isPartyMember': '',
                    'isAll': ''
                }
                await unlock()
                try:
                    youth_data = (await httpx_get(
                        # url="https://www.sxgqt.org.cn/bgsxapiv2/regiment",
                        url="https://api.sxgqt.org.cn/bgsxapiv2/regiment",
                        headers=headers,
                        params=params
                    )).json()
                except AttributeError:
                    youth_data = None
                    await youth_checker.finish("服务器繁忙，请过会儿再来捏~\n【发生了什么？】\n    我已经为您成功登录平台\n    但在查询数据时出现了错误\n    "
                                               "这可能是由于双方任一服务器网络波动造成的（我的可能性比较大）\n【我该怎么办？】\n   足下可以稍后再来哦，么~")
                if youth_data:
                    await async_w(YOUTH_DATA_PATH, json.dumps(youth_data, ensure_ascii=False))
                    isStudy, unfinished = await youth_analyze(youth_data)
                    l_IS = len(isStudy)
                    l_UF = len(unfinished)
                    is_text = ""
                    un_text = ""
                    for i in isStudy:
                        is_text += f"{i}\n"
                    for i in unfinished:
                        un_text += f"{i}\n"
                    # FIXME 不要问为什么总人数下面不都用三个字来格式化，因为会风控
                    r = "本次大学习统计如下：\n" \
                        f"总人数：{youth_data['data']['total']}\n" \
                        f"已学：{l_IS}\n" \
                        f"未学：{l_UF}\n" \
                        f"学习率：{round(l_IS / int(youth_num) * 100, 2)}%\n"
                    if l_IS > 0:
                        r += f"已完成名单：\n{is_text}"
                        r += f"{'-'*20}\n"
                    if l_UF > 0:
                        r += f"未完成名单：\n{un_text}\n{'-'*20}\n"
                        r += f"别让等待，成为遗憾\n青年大学习 {l_IS} 等 {l_UF} "
                    elif l_UF == 0:
                        r += "蚌！所有人都学啦！"

                    if state["mode"] == "normal":
                        await youth_checker.finish(r)

                    elif state["mode"] == "at":
                        if YOUTH_QQ_PATH.exists():
                            qq_info = json.loads(YOUTH_QQ_PATH.read_text(encoding="utf-8"))
                            for name in unfinished:
                                if name in qq_info:
                                    r += MessageSegment.at(qq_info[name])
                            await youth_checker.finish(r)
                        else:
                            logger.info("未找到姓名-QQ对应文件,使用普通模式")
                            await youth_checker.finish(r)
    except (FinishedException, RejectedException):
        await unlock()
        pass
    except Exception as e:
        await unlock()
        logger.error(e)
        await youth_checker.finish("发生了未知错误，请重试")


un_lock = on_command("解锁", aliases={"解锁青年大学习"}, priority=5, block=True)


@un_lock.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await unlock()
    await bot.send("完成")


async def unlock():
    LOCK_PATH.unlink() if LOCK_PATH.exists() else None
