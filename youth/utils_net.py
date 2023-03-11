# python3
# -*- coding: utf-8 -*-
# @Time    : 2022/9/6 20:10
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : utils_net.py
# @Software: PyCharm
import os
import json
from typing import Dict, Union, Optional, Tuple

from httpx import Response
from playwright._impl._api_types import TimeoutError

import httpx
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from nonebot import logger
from .utils import *
from .path import *


async def httpx_get(url: str, headers: Dict = None, cookies: Dict[str, str] = None, params: Dict = None) -> Optional[
    Response]:
    """
    httpx get请求
    :param headers: 请求头
    :param params: 查询参数
    :param url: 请求地址
    :param cookies: cookies
    :return:
    """
    try:
        async with httpx.AsyncClient(cookies=cookies, headers=headers) as client:
            r = await client.get(url, params=params)
            return r
    except Exception as e:
        logger.warning(f"请求失败 {type(e)}：{e}")
        return None


async def httpx_post(
        url: str,
        headers: Dict[str, str] = None,
        cookies: Dict[str, str] = None,
        data: Dict[str, str] = None,
        type_: str = "json",
) -> Optional[str]:
    """
    httpx post请求
    :param headers: headers
    :param url: 请求地址
    :param cookies: cookies
    :param data: post数据
    :param type_: 返回类型
    :return:
    """
    try:
        async with httpx.AsyncClient(cookies=cookies, headers=headers) as client:
            r = await client.post(url, data=data)
            if type_ == "json":
                return r.json()
            else:
                return r.text
    except Exception as e:
        logger.warning(f"请求失败 {type(e)}：{e}")
        return None


@time_log
async def get_main_cookies(context: BrowserContext, page: Page, account: str, password: str, verify: str):
    """
    获取主站cookies
    :return:
    """

    try:
        await page.locator("[placeholder=\"请输入账号\"]").fill(account)
        await page.locator("[placeholder=\"请输入密码\"]").fill(password)
        await page.locator("[placeholder=\"请输入验证码\"]").fill(verify)
        await page.locator("button:has-text(\"登 录\")").click()
        await page.wait_for_url("https://www1.sxgqt.org.cn/bgsxv2/reunion/member/memberList")
        html = await page.content()
        await context.storage_state(path=AUTH_PATH)
        await page.close()
        auth = json.loads(AUTH_PATH.read_text())
        cookies = auth["cookies"]
        getToken = False
        token = None
        for cookie in cookies:
            if cookie["name"] == "token":
                getToken = True
                token = cookie["value"]
        if getToken:
            return token
        else:
            logger.warning("登陆失败")

        await context.close()


    except TimeoutError:
        logger.warning("操作超时，请重试")
        await context.close()
        raise OperationTimedOutError


# context: BrowserContext,
async def playwright_login() -> Union[tuple[BrowserContext, Page], str]:
    browser = await browser_init()
    context = await browser.new_context(locale="zh-CN")
    page = await context.new_page()
    try:
        await page.goto("https://www1.sxgqt.org.cn/bgsxv2/login?redirect=%2Freunion%2Fmember%2FmemberList")
        img = await page.locator('//*[@id="pane-first"]/div/div/form/div[3]/div/img').screenshot(type="jpeg",
                                                                                                 path=VERIFY_PATH / "verify.jpg",
                                                                                                 quality=100)
        return context, page

    except TimeoutError:
        return "TimeoutError"


class OperationTimedOutError(Exception):
    pass
