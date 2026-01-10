import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode

async def _fetch_text(session, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
            print(f"Fetching {url}, status: {response.status}")
            if response.status == 200:
                return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

async def test_gov_search(site_url, keyword):
    async with aiohttp.ClientSession() as session:
        print(f"--- Testing {site_url} ---")
        html = await _fetch_text(session, site_url)
        if not html:
            print("Failed to fetch homepage")
            return

        soup = BeautifulSoup(html, 'html.parser')
        search_form = None
        search_input_name = None
        
        forms = soup.find_all('form')
        print(f"Found {len(forms)} forms")
        
        for form in forms:
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name')
                print(f"  Form action: {form.get('action')}, Input: {name}")
                if name and name.lower() in ['q', 'wd', 'query', 'key', 'keyboard', 'search', 'keywords', 's', 't']:
                    search_form = form
                    search_input_name = name
                    print(f"  -> MATCHED search form! Input name: {name}")
                    break
            if search_form:
                break
        
        if not search_form:
            print("No search form found via auto-discovery.")
            # Fallback test for hardcoded known endpoints
            if "gov.cn" in site_url:
                 # Try specific gov.cn search
                 target_url = "https://sousuo.www.gov.cn/sousuo/search.shtml"
                 params = {"q": keyword, "t": "govall"}
                 print(f"Trying hardcoded endpoint: {target_url} with params {params}")
                 full_url = target_url + "?" + urlencode(params)
                 res_html = await _fetch_text(session, full_url)
                 if res_html:
                     print(f"Got results page, length: {len(res_html)}")
                     # Parse links
                     res_soup = BeautifulSoup(res_html, 'html.parser')
                     links = res_soup.find_all('a', href=True)
                     found_count = 0
                     for link in links:
                         if keyword in link.get_text():
                             found_count += 1
                             print(f"  Found result: {link.get_text().strip()} -> {link.get('href')}")
                     print(f"Total relevant links found: {found_count}")
            return

        # ... rest of the original logic if form found ...

if __name__ == "__main__":
    asyncio.run(test_gov_search("https://www.gov.cn", "工业互联网"))
    asyncio.run(test_gov_search("https://www.miit.gov.cn", "工业互联网"))
