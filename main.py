import asyncio
from playwright.async_api import async_playwright
from humantyping import HumanTyper
from loguru import logger

from navigation import target_list, attack_target, write_words

@logger.catch
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("https://s0urce.io", wait_until="domcontentloaded")

        typer = HumanTyper(wpm=90)
        
        name_input = page.get_by_placeholder("Enter name")

        await asyncio.sleep(2)

        await name_input.click()
        await typer.type(name_input, "Anon102")

        play_button = page.get_by_role("button", name="Play")
        await play_button.click()

        await asyncio.sleep(3)

        targets = await target_list(page)

        await asyncio.sleep(2)

        await attack_target(page, targets[0])
        
        await asyncio.sleep(5)

        await write_words(page)

        await asyncio.sleep(10)

        # await page.wait_for_selector('.target-bar-progress[style*="width: 100%"]')
        # for future reference knowing when the bar is full

        await browser.close()

asyncio.run(main())