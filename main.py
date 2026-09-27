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

        """Basic Loop will be:
        Get Target > Attack Target > Repeat

        """

        attack = True

        while attack:
            targets = await target_list(page)
            await asyncio.sleep(0.5)

            if targets:
                await attack_target(page, targets[0])
                await asyncio.sleep(0.5)

                progress_bar = page.locator('.target-bar-progress')
                
                while True:
                    style = await progress_bar.get_attribute('style') or ''
                    
                    if 'width: 100%' in style:
                        break
                    
                    await write_words(page)
                    await asyncio.sleep(0.5)

            await asyncio.sleep(1)

        await browser.close()

asyncio.run(main())