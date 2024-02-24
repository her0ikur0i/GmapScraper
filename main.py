import asyncio
import os
import csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Import browser from pyppeteer
from pyppeteer import launch

async def searchGoogleMaps():
    try:
        # Define search query
        query = "Nasi Goreng, Bandung"

        # Define file path
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nasgor_bdg.csv')

        # Launch browser
        browser = await launch(headless=False, executablePath="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")

        # Create new page
        page = await browser.newPage()

        # Navigate to Google Maps search URL
        await page.goto(f'https://www.google.com/maps/search/{"+".join(query.split())}', timeout=480000)

        await page.waitForSelector('div[role="feed"]')

        # Scroll to load more results
        await autoScroll(page)

        # Get HTML content
        html = await page.content()
        await browser.close()

        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find relevant elements
        businesses = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and "/maps/place/" in href:
                parent = link.parent
                url = href
                website_elem = parent.find('a', attrs={'data-value': 'Website'})
                website = website_elem.get('href') if website_elem else None
                storeName_elem = parent.find('div', class_='fontHeadlineSmall')
                storeName = storeName_elem.get_text() if storeName_elem else None
                ratingText_elem = parent.find('span', class_='fontBodyMedium')
                ratingText = ratingText_elem.get_text() if ratingText_elem else None
                address_elem = parent.find('div', class_='fontBodyMedium')
                address = address_elem.get_text().split('·')[1].strip() if address_elem and len(address_elem.get_text().split('·')) > 1 else None
                phone = address_elem.get_text().split('·')[2].strip() if address_elem and len(address_elem.get_text().split('·')) > 2 else None

                # Replace comma with dot before converting to float
                ratingText = ratingText.replace(',', '.')

                # Handling non-numeric rating
                try:
                    stars = float(ratingText.split(' ')[0])
                    numberOfReviews = int(ratingText.split(' ')[1].replace(',', ''))
                except ValueError:
                    stars = None
                    numberOfReviews = None

                verified_elem = parent.find('span', class_='bSM')
                verified = "Ya" if verified_elem else "Tidak"

                businesses.append({
                    'Nama': storeName,
                    'Kategori': address_elem.get_text().split('·')[0].strip() if address_elem and len(address_elem.get_text().split('·')) > 0 else None,
                    'Telepon': phone,
                    'Website': website,
                    'Alamat': address,
                    'Rating': stars,
                    'Link Google Map': f'https://www.google.com{url}',
                    'Verified': verified
                })

        # Define fieldnames in desired order
        fieldnames = ['Nama', 'Kategori', 'Telepon', 'Website', 'Alamat', 'Rating', 'Link Google Map', 'Verified']

        # Write data to CSV file
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for business in businesses:
                writer.writerow(business)

        print("Data has been saved to", file_path)

    except Exception as e:
        print("Error at searchGoogleMaps:", e)

async def autoScroll(page):
    await page.evaluate('''async () => {
        await new Promise((resolve, reject) => {
            var totalHeight = 0;
            var distance = 1000;
            var scrollDelay = 3000;

            var timer = setInterval(async () => {
                var wrapper = document.querySelector('div[role="feed"]');
                var scrollHeightBefore = wrapper.scrollHeight;
                wrapper.scrollBy(0, distance);
                totalHeight += distance;

                if (totalHeight >= scrollHeightBefore) {
                    totalHeight = 0;
                    await new Promise((resolve) => setTimeout(resolve, scrollDelay));

                    // Calculate scrollHeight after waiting
                    var scrollHeightAfter = wrapper.scrollHeight;

                    if (scrollHeightAfter > scrollHeightBefore) {
                        // More content loaded, keep scrolling
                        return;
                    } else {
                        // No more content loaded, stop scrolling
                        clearInterval(timer);
                        resolve();
                    }
                }
            }, 200);
        });
    }''')

async def main():
    await searchGoogleMaps()

asyncio.get_event_loop().run_until_complete(main())
