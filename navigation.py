import asyncio
from playwright.async_api import async_playwright, Page
from loguru import logger
from image_matcher import get_image_word
from humantyping import HumanTyper

async def target_list(page: Page):
    await page.get_by_text("Target List", exact=True).click()

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
        word = get_image_word(source)
        await typer.type(input_field, word+" ")
