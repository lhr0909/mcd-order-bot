import random
from Levenshtein import distance
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright, Playwright, Browser, Page
import shortuuid
import cv2
import numpy as np

from typing import Any, Dict, List, Optional, Tuple

app = FastAPI()

playwright = async_playwright()

qr_decoder = cv2.QRCodeDetector()

sessions: Dict[str, Tuple[Playwright, Browser, Page, str]] = {}

class SessionInput(BaseModel):
    session_id: Optional[str] = None
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
    session_id = input.session_id if input.session_id is not None else 'test'
    # session_id = shortuuid.uuid()
    session = await playwright.start()
    browser = await session.chromium.launch_persistent_context(
        headless=False,
        user_data_dir='./browsercache',
        devtools=True,
        viewport={
            'width': 1600,
            'height': 900,
        },
    )
    page = browser.pages[0]
    # page = await browser.new_page()
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
            titles = await page.eval_on_selector_all(
                '//div[@class="buy-box"]/div[@class="left"]/p',
                '(boxes) => boxes.map(box => box.innerText)',
            )

            distances = [distance(input.query, x) for x in titles]
            item_matches = sorted(zip(titles, distances, range(1, len(titles) + 1)), key=lambda x: x[1])
            print(item_matches)

            if len(item_matches) > 0:
                # select the closest one
                button_selector = f'(//div[@class="buy-box"])[{item_matches[0][2]}]/*[contains(@class, "button")]'
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
                    await page.goto('https://mcd.cn/product')
                    # await page.click('div:text("餐品菜单")')
                    items.append({'name': item_title, 'quantity': input.quantity})
        else:
            result_count = await page.eval_on_selector_all(
                '//div[@class="buy-box"]/div[@class="left"]/p',
                '(boxes) => boxes.length',
            )

            # pick one at random
            item_idx = random.sample(range(1, result_count + 1), input.quantity)

            for idx in item_idx:
                button_selector = f'(//div[@class="buy-box"])[{idx}]/*[contains(@class, "button")]'
                button_class_dict: Dict[str, str] = await page.eval_on_selector(
                    button_selector,
                    '(button) => button.classList',
                )

                if 'custom' not in button_class_dict.values():
                    # just click on the button
                    await page.click(button_selector, click_count=1)
                    item_title = await page.eval_on_selector(
                        '(//div[@class="buy-box"])[1]/div[@class="left"]/p',
                        '(title) => title.innerText',
                    )
                    items.append({'name': item_title, 'quantity': 1})
                else:
                    # go into customization
                    await page.click(button_selector)
                    await page.wait_for_timeout(500)
                    # get the first sub-item
                    item_title = await page.eval_on_selector(
                        '(//h1[@class="title"])[1]',
                        '(title) => title.innerText',
                    )
                    await page.fill('//input[contains(@class, "count")]', '1')
                    await page.wait_for_timeout(500)
                    await page.click('button.to-cart')
                    await page.wait_for_timeout(1000)
                    items.append({'name': item_title, 'quantity': 1})

                    # await page.click('div:text("餐品菜单")')
                    await page.goto('https://mcd.cn/product')

                    await page.wait_for_timeout(2000)
                    await page.fill('//input[contains(@placeholder, "最多")]', input.query)
                    await page.click('button.ant-input-search-button')
                    await page.wait_for_timeout(1000)

        state = 'ordered'
        metadata = {'items': items}
        sessions[session_id] = (session, browser, page, state)
        return SessionOutput(id=session_id, state=state, metadata=metadata)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.post('/sessions/{session_id}/cart/clear', response_model=SessionOutput)
async def clear_session_cart(session_id: str):
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
async def get_session_cart(session_id: str):
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
        checkout_button_class_dict: Dict[str, str] = await page.eval_on_selector(
            '//button[contains(@class, "to-check")]',
            '(button) => button.classList',
        )
        if 'grey' in checkout_button_class_dict.values():
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
                    'items': list(map(lambda item: { "name": item[0], "quantity": item[1] }, zip(item_titles, item_quantities))),
                    'cart_price_texts': cart_price_texts,
                    'address_texts': address_texts,
                    'deliver_time_texts': deliver_time_texts,
                },
            )
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.post('/sessions/{session_id}/checkout', response_model=SessionOutput)
async def checkout_session(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        await page.click('//button[contains(@class, "to-check")]')
        await page.wait_for_timeout(2000)
        await page.click('button.btn-pay')
        await page.wait_for_timeout(500)
        await page.click('p:text("支付宝")')
        await page.wait_for_timeout(500)
        await page.click('button.sure')
        await page.wait_for_timeout(5000)
        payment_page: Page = browser.pages[1]
        screenshot = await payment_page.screenshot(full_page=True)
        bytes_as_np_array = np.frombuffer(screenshot, dtype=np.uint8)
        img = cv2.imdecode(bytes_as_np_array, cv2.IMREAD_ANYCOLOR)
        qr_data, bbox, rectified_image = qr_decoder.detectAndDecode(img)
        # if len(qr_data) > 0:
        #     rectified_image = np.uint8(rectified_image)
        #     cv2.startWindowThread()
        #     cv2.imshow('qr', rectified_image)
        #     cv2.waitKey()
        state = 'payment_triggered'
        metadata = {'payment_qr_url': qr_data}
        sessions[session_id] = (session, browser, page, state)
        # await page.wait_for_timeout(1000)
        # await page.click('div.payFooterContainer > button.sure') # on success
        # await page.click('div.payFooterContainer > button.defaultBtn') # on failure
        return SessionOutput(id=session_id, state=state, metadata=metadata)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.post('/sessions/{session_id}/checkout/retry', response_model=SessionOutput)
async def checkout_session_retry(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        if len(browser.pages) > 1:
            payment_page: Page = browser.pages[1]
            screenshot = await payment_page.screenshot(full_page=True)
            bytes_as_np_array = np.frombuffer(screenshot, dtype=np.uint8)
            img = cv2.imdecode(bytes_as_np_array, cv2.IMREAD_ANYCOLOR)
            qr_data, bbox, rectified_image = qr_decoder.detectAndDecode(img)
            state = 'payment_triggered'
            metadata = {'payment_qr_url': qr_data}
            sessions[session_id] = (session, browser, page, state)
            return SessionOutput(id=session_id, state=state)
        else:
            await page.click('div.payFooterContainer > button.defaultBtn') # on failure
            await page.wait_for_timeout(500)
            await page.click('button.sure')
            await page.wait_for_timeout(5000)
            payment_page: Page = browser.pages[1]
            screenshot = await payment_page.screenshot(full_page=True)
            bytes_as_np_array = np.frombuffer(screenshot, dtype=np.uint8)
            img = cv2.imdecode(bytes_as_np_array, cv2.IMREAD_ANYCOLOR)
            qr_data, bbox, rectified_image = qr_decoder.detectAndDecode(img)
            state = 'payment_triggered'
            metadata = {'payment_qr_url': qr_data}
            sessions[session_id] = (session, browser, page, state)
            return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.post('/sessions/{session_id}/checkout/success', response_model=SessionOutput)
async def checkout_session_success(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        if len(browser.pages) > 1:
            payment_page: Page = browser.pages[1]
            await payment_page.close()
            await page.wait_for_timeout(1000)
            await page.click('div.payFooterContainer > button.sure') # on success
            # await page.click('div.payFooterContainer > button.defaultBtn') # on failure
        state = 'payment_success'
        sessions[session_id] = (session, browser, page, state)
        return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')

@app.get('/sessions/{session_id}', response_model=SessionOutput)
async def get_session(session_id: str):
    try:
        session, browser, page, state = sessions[session_id]
        return SessionOutput(id=session_id, state=state)
    except KeyError:
        raise HTTPException(state_code=404, detail='session not found')
