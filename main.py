import asyncio
from playwright.async_api import async_playwright
from humantyping import HumanTyper
from loguru import logger

@logger.catch
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("https://s0urce.io", wait_until="domcontentloaded")

        typer = HumanTyper(wpm=90)
        
        name_input = page.get_by_placeholder("Enter name")

        await name_input.click()
        await typer.type(name_input, "Anon102")

        play_button = page.get_by_role("button", name="Play")
        await play_button.click()
        
        await asyncio.sleep(2)  # Pause briefly to see the result
        await browser.close()

asyncio.run(main())