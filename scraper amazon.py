import time
import pandas as pd
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

search_query = input("Enter the product you want to search: ").strip()
if not search_query:
    print("No product entered. Exiting.")
    exit()

search_query_encoded = quote_plus(search_query)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-US"
    )
    page = context.new_page()

    url = f"https://www.amazon.in/s?k={search_query_encoded}"
    print(f"🔎 Searching Amazon for: {search_query}")
    page.goto(url, timeout=60000, wait_until="domcontentloaded")
    time.sleep(3)  

    if "captcha" in page.url.lower():
        print("❌ CAPTCHA detected! Cannot scrape automatically.")
        browser.close()
        exit()

    html = page.content()  
    

soup = BeautifulSoup(html, "html.parser")
product_containers = soup.find_all("div", {"data-component-type": "s-search-result"})
print("✅ Number of product containers found:", len(product_containers))

results = []

for i, product in enumerate(product_containers):
    name_tag = product.h2
    name = name_tag.text.strip() if name_tag else "N/A"

    try:
        url_tag = name_tag.a["href"]
        product_url = "https://www.amazon.in" + url_tag
    except:
        product_url = "N/A"

    price_tag = product.find("span", class_="a-price-whole")
    price_fraction = product.find("span", class_="a-price-fraction")
    if price_tag:
        price = price_tag.text.strip()
        if price_fraction:
            price += price_fraction.text.strip()
    else:
        price = "N/A"

    rating_tag = product.find("span", class_="a-icon-alt")
    rating = rating_tag.text.strip() if rating_tag else "N/A"

    review_tag = product.find("span", {"class": "a-size-base"})
    review = review_tag.text.strip() if review_tag else "N/A"

    results.append({
        "Name": name,
        "Price": price,
        "Rating": rating,
        "Reviews": review,
        "URL": product_url
    })

    if i < 3:
        print(f"🔹 Product {i+1}: {name} | {price} | {rating} | {review} | {product_url}")

if results:
    df = pd.DataFrame(results)
    print("\n✅ Sample results:")
    print(df.head(10))
    df.to_csv(f"{search_query}_amazon.csv", index=False, encoding="utf-8-sig")
    print(f"✅ Data saved to {search_query}_amazon.csv")
else:
    print("❌ No products found.")