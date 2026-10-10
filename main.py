import asyncio
from playwright.async_api import async_playwright
from humantyping import HumanTyper
from loguru import logger

from navigation import target_list, attack_target, write_words, get_tries_count
from image_matcher import log_failed_attempt

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

        await page.locator("#desktop-container").get_by_text("Target List", exact=True).click()
        await asyncio.sleep(1.5)

        attack = True

        while attack:
            targets = await target_list(page)
            await asyncio.sleep(0.5)

            if not targets:
                logger.info("No valid targets available.")
                await asyncio.sleep(1)
                continue

            await attack_target(page, targets[0])
            await asyncio.sleep(0.5)

            tries = await get_tries_count(page)
            logger.info(f"Initial tries for target: {tries}")

            progress_bar = page.locator('.target-bar-progress')

            while True:
                style = await progress_bar.get_attribute('style') or ''
                if 'width: 100%' in style:
                    logger.success("Hack complete (100%)!")
                    break

                await write_words(page)
                await asyncio.sleep(0.5)

                current_tries = await get_tries_count(page)

                if current_tries is not None and tries is not None:
                    if current_tries < tries:
                        logger.warning(f"Tries decreased: {tries} -> {current_tries}")
                        log_failed_attempt()
                    tries = current_tries

                if tries == 0:
                    logger.error("Tries reached 0! Stopping attempt on this target.")
                    break

            if tries is not None and tries > 0:
                message_input = page.locator('.window:has-text("Hacked Player") div[contenteditable="true"]')
                await message_input.press("Enter")

                await asyncio.sleep(1)
            else:
                terminal_close_button = page.locator('.window:has-text("Terminal") .window-close')
                await terminal_close_button.click()
                
            await asyncio.sleep(1)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())