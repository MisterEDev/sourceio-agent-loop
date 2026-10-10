import asyncio
from playwright.async_api import async_playwright, Page
from loguru import logger
from image_matcher import get_image_word
from humantyping import HumanTyper

async def target_list(page: Page):
    taskbar_item = page.locator('#taskbar').get_by_text("Target List", exact=True)
    await taskbar_item.dispatch_event("click")

    rows = page.locator("#list > div.wrapper")
    await rows.first.wait_for()
    count = await rows.count()

    targets = []

    for i in range(count):
        row = rows.nth(i)

        class_attribute = await row.get_attribute("class") or ""

        if "is-you" in class_attribute or "npc-premium" in class_attribute or await row.locator("div.timer-text").count() > 0:
            continue

        targets.append(row)

    return targets

async def attack_target(page: Page, target):
    await target.click()

    await page.get_by_alt_text("Hack").click()

    await page.get_by_role("button", name="Port 21").click()

async def write_words(page: Page):
    typer = HumanTyper(wpm=90)

    image_locator = page.locator('#word-to-type img')
    input_field = page.locator('#section-type input[name="input"]')

    count = image_locator.count()
    
    if await count > 0:
        sources = await image_locator.evaluate_all("imgs => imgs.map(img => img.getAttribute('src'))")
        logger.info(f"Found {len(sources)} image(s) inside #word-to-type")
    else:
        logger.warning("No image found inside #word-to-type")

    for source in sources:
        try:
            word = await asyncio.wait_for(
                asyncio.to_thread(get_image_word, source),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error("AI request timed out after 30 seconds! Skipping image.")
            word = ""
        except Exception as e:
            logger.error(f"Error resolving image: {e}")
            word = ""

        if word:
            await input_field.fill('')
            await typer.type(input_field, word)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.3)

async def get_tries_count(page: Page) -> int | None:
    tries_locator = page.locator('#section-target div', has_text="Tries:")
    
    if await tries_locator.count() > 0:
        raw_text = await tries_locator.last.inner_text()
        
        try:
            value_str = raw_text.split(":")[-1].strip()
            return int(value_str)
        except (ValueError, IndexError):
            logger.warning(f"Failed to parse integer from string: '{raw_text}'")
            return None
            
    return None