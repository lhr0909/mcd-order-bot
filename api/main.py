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
    session_id = 'test'
    # session_id = shortuuid.uuid()
    session = await playwright.start()
    browser = await session.chromium.launch_persistent_context(
        headless=False,
        user_data_dir='./browsercache',
        devtools=True,
    )
    page = await browser.new_page()
    await page.goto('https://mcd.cn')
    await page.click('div.language')
    await page.click('div.languageList > div.title:text("简体中文")')
    await page.wait_for_timeout(1000)

    await page.click('span:text("开始订餐")')
    state = 'logged_in'

    # await page.click('div.treaty-plane > img')
    # await page.fill('input.txt-phone', input.phone)
    # await page.click('button.countDownBtn')
    # state = 'requested_code'
    sessions[session_id] = (session, browser, page, state)
    return SessionOutput(id=session_id, state=state)

@app.post('/sessions/{session_id}/login', response_model=SessionOutput)
async def login_session(session_id: str, input: LoginInput):
    try:
        session, browser, page, state = sessions[session_id]
        await page.fill('input.txt-sms', input.code)
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
        await page.fill('//input[contains(@placeholder, "最多")]', input.query)
        await page.click('button.ant-input-search-button')

        await page.wait_for_timeout(1000)

        items: List[Dict[str, Any]] = []

        if input.is_exact is True:
            # loop through the items and try to match the name
            # titles = await page.eval_on_selector_all(
            #     '//div[@class="buy-box"]/div[@class="left"]/p',
            #     '(boxes) => boxes.map(box => box.innerText)',
            # )

            # select the first one
            button_selector = '(//div[@class="buy-box"])[1]/*[contains(@class, "button")]'
            button_class_dict: Dict[str, str] = await page.eval_on_selector(
                button_selector,
                '(button) => button.classList',
            )

            if 'custom' not in button_class_dict.values():
                # just click on the button
                await page.click(button_selector, click_count=input.quantity)
                item_title = await page.eval_on_selector(
                    '(//div[@class="buy-box"])[1]/div[@class="left"]/p',
                    '(title) => title.innerText',
                )
                items.append({'name': item_title, 'quantity': input.quantity})
            else:
                # go into customization
                await page.click(button_selector)
                await page.wait_for_timeout(500)
                # get the first sub-item
                item_title = await page.eval_on_selector(
                    '(//h1[@class="title"])[1]',
                    '(title) => title.innerText',
                )
                await page.fill('//input[contains(@class, "count")]', str(input.quantity))
                await page.wait_for_timeout(500)
                await page.click('button.to-cart')
                await page.wait_for_timeout(1000)
                await page.click('div:text("餐品菜单")')
                items.append({'name': item_title, 'quantity': 1})
        else:
            result_count = await page.eval_on_selector_all(
                '//div[@class="buy-box"]/div[@class="left"]/p',
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

@app.post('/sessions/{session_id}/cart/clear', response_model=SessionOutput)
async def clear_cart(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        await page.click('//div[@class="car"]')
        await page.wait_for_timeout(500)
        await page.click('span:text("清空购物车")')
        await page.wait_for_timeout(500)
        await page.click('//div[@class="ant-popover-buttons"]/button[contains(@class, "ant-btn-primary")]')
        state = 'cart_cleared'
        sessions[session_id] = (session, browser, page, state)
        return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.get('/sessions/{session_id}/cart', response_model=SessionOutput)
async def get_cart(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        cart_price_texts = await page.eval_on_selector_all(
            '//div[@class="price-info"]/span',
            '(spans) => spans.map((span) => span.innerText)',
        )
        address_texts = await page.eval_on_selector_all(
            '//div[@class="othpart address"]/div[@class="center"]/div',
            '(spans) => spans.map((span) => span.innerText)',
        )
        deliver_time_texts = await page.eval_on_selector_all(
            '//div[@class="othpart time"]/div[@class="center"]/div',
            '(spans) => spans.map((span) => span.innerText)',
        )
        checkout_button: Dict[str, str] = await page.eval_on_selector(
            '//button[contains(@class, "to-check")]',
            '(button) => button.classList',
        )
        if 'grey' in checkout_button.values():
            state = 'cart_empty'
            sessions[session_id] = (session, browser, page, state)
            return SessionOutput(
                id=session_id,
                state=state,
                metadata={
                    'items': [],
                    'cart_price_texts': cart_price_texts,
                    'address_texts': address_texts,
                    'deliver_time_texts': deliver_time_texts,
                },
            )
        else:
            await page.click('//div[@class="car"]')
            await page.wait_for_timeout(500)
            item_titles = await page.eval_on_selector_all(
                '//div[contains(@class, "cart-panel-details")]/div[@class="main"]/div/div/div[@class="name"]',
                '(titles) => titles.map(title => title.innerText)',
            )
            item_quantities = await page.eval_on_selector_all(
                '//div[contains(@class, "cart-panel-details")]/div[@class="main"]/div/div/div[@class="count-panel"]/div/input',
                '(quantities) => quantities.map(q => q.value)',
            )
            await page.wait_for_timeout(500)
            await page.click('//div[@class="close"]')

            state = 'cart_viewed'
            sessions[session_id] = (session, browser, page, state)
            return SessionOutput(
                id=session_id,
                state=state,
                metadata={
                    'items': tuple(zip(item_titles, item_quantities)),
                    'cart_price_texts': cart_price_texts,
                    'address_texts': address_texts,
                    'deliver_time_texts': deliver_time_texts,
                },
            )
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.get('/sessions/{session_id}', response_model=SessionOutput)
async def get_session(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')
