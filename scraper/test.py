# import asyncio
# from bs4 import BeautifulSoup
# from playwright.async_api import async_playwright


# async def get_talos_category(domain):
#     url = f"https://talosintelligence.com/reputation_center/lookup?search={domain}"

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(
#             headless=False
#         )  # Set headless=False to see browser
#         page = await browser.new_page()
#         await page.goto(url, timeout=600000)

#         # Wait until category table is loaded
#         await page.wait_for_selector("td.content-category", timeout=150000)

#         html = await page.content()
#         await browser.close()

#         soup = BeautifulSoup(html, "html.parser")
#         td = soup.find("td", class_="content-category")

#         if td:
#             categories = [text.strip() for text in td.stripped_strings]
#             return {"domain": domain, "categories": categories}
#         else:
#             return {
#                 "domain": domain,
#                 "categories": None,
#                 "note": "Category not found in page",
#             }


# # Entry point
# if __name__ == "__main__":
#     domain_to_check = "xvideos.com"
#     result = asyncio.run(get_talos_category(domain_to_check))
#     print(result)
