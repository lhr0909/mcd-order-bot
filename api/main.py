from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright, Playwright, Browser, Page
import shortuuid

from typing import Any, Dict, List, Optional, Tuple

app = FastAPI()

playwright = async_playwright()

sessions: Dict[str, Tuple[Playwright, Browser, Page, str]] = {}

class SessionInput(BaseModel):
    phone: str

class LoginInput(BaseModel):
    code: str

class OrderInput(BaseModel):
    query: str
    quantity: int
    is_exact: bool

class SessionOutput(BaseModel):
    id: str
    state: str
    metadata: Optional[Dict[str, Any]] = None

@app.get('/')
async def root():
    return {'status': 'OK'}

@app.post('/sessions', response_model=SessionOutput)
async def create_session(input: SessionInput):
    session_id = shortuuid.uuid()
    session = await playwright.start()
    browser = await session.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto('https://mcd.cn')
    await page.click('div.language')
    await page.click('div.languageList > div.title:text("简体中文")')
    await page.click('div.treaty-plane > img')
    await page.type('input.txt-phone', input.phone)
    await page.click('button.countDownBtn')
    state = 'requested_code'
    sessions[session_id] = (session, browser, page, state)
    return SessionOutput(id=session_id, state=state)

@app.post('/sessions/{session_id}/login', response_model=SessionOutput)
async def login_session(session_id: str, input: LoginInput):
    try:
        session, browser, page, state = sessions[session_id]
        await page.type('input.txt-sms', input.code)
        await page.click('button.login-button')
        await page.wait_for_timeout(1000)
        await page.click('span:text("开始订餐")')
        state = 'logged_in'
        sessions[session_id] = (session, browser, page, state)
        return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.post('/sessions/{session_id}/order', response_model=SessionOutput)
async def order_session(session_id: str, input: OrderInput):
    try:
        session, browser, page, state = sessions[session_id]
        await page.type('//input[contains(@placeholder, "最多")]', input.query)
        await page.click('button.ant-input-search-button')

        items: List[Dict[str, Any]] = []
        if input.is_exact is True:
            # loop through the items and try to match the name
            titles = await page.eval_on_selector_all(
                'xpath=//div[@class="buy-box"]/div[@class="left"]/p',
                '(boxes) => boxes.map(box => box.innerText)',
            )
            print(titles)
            # items.append({'name': name, 'quantity': 1})
        else:
            result_count = await page.eval_on_selector_all(
                'xpath=//div[@class="buy-box"]/div[@class="left"]/p',
                '(boxes) => boxes.length',
            )
            # pick one at random
            print(result_count)
            # items.append({'name': name, 'quantity': 1})

        state = 'ordered'
        metadata = {'items': items}
        sessions[session_id] = (session, browser, page, state)
        return SessionOutput(id=session_id, state=state, metadata=metadata)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.get('/sessions/{session_id}', response_model=SessionOutput)
async def get_session(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')
