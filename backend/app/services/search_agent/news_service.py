import asyncio
import aiohttp
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.config import settings
from app.schemas.search_agent.news_schemas import NewsItem, NewsSearchRequest, NewsSearchResponse, CustomNewsSearchRequest
from app.services.search_agent.search_service import perform_search, perform_tavily_search

async def _fetch_text(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    try:
        async with session.get(url, headers=headers, timeout=10, ssl=False) as response:
            if response.status == 200:
                content = await response.read()
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return content.decode('gbk')
                    except:
                        return content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

async def _search_gov_site_tier1(session: aiohttp.ClientSession, site_url: str, keyword: str, target_date: Optional[str] = None) -> List[NewsItem]:
    """
    Tier 1: Core In-Site Search
    Strategy: Simulate in-site search form submission
    """
    results = []
    try:
        html = await _fetch_text(session, site_url)
        if not html:
            return results

        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Find Search Form
        search_form = None
        search_input_name = None
        
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all('input')
            for inp in inputs:
                if inp.get('type') in ['text', 'search'] or not inp.get('type'):
                    name = inp.get('name')
                    if name and name.lower() in ['q', 'wd', 'query', 'key', 'keyboard', 'search', 'keywords', 's']:
                        search_form = form
                        search_input_name = name
                        break
            if search_form:
                break
        
        if not search_form:
            return results

        # 2. Construct Search Request
        action = search_form.get('action') or ""
        method = (search_form.get('method') or "get").lower()
        target_url = urljoin(site_url, action)
        
        params = {}
        for inp in search_form.find_all('input'):
            if inp.get('type') == 'hidden' and inp.get('name'):
                params[inp.get('name')] = inp.get('value', '')
        
        # Use simple keyword for form submission, as advanced query syntax support is unknown
        params[search_input_name] = keyword
        
        search_html = None
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if method == 'post':
            async with session.post(target_url, data=params, headers=headers, timeout=10, ssl=False) as resp:
                if resp.status == 200:
                    search_html = await resp.text()
        else:
            if '?' in target_url:
                target_url += '&' + urlencode(params)
            else:
                target_url += '?' + urlencode(params)
            search_html = await _fetch_text(session, target_url)

        if not search_html:
            return results

        # 3. Parse Results
        res_soup = BeautifulSoup(search_html, 'html.parser')
        links = res_soup.find_all('a', href=True)
        
        seen_urls = set()
        for link in links:
            href = link.get('href')
            full_url = urljoin(target_url, href)
            text = link.get_text().strip()
            
            if full_url in seen_urls:
                continue
            
            if urlparse(full_url).netloc != urlparse(site_url).netloc:
                continue
                
            if len(text) > 10 and (keyword in text or len(text) > 20):
                # Basic date check if present in text
                if target_date and target_date not in text and target_date.replace('-', '') not in text:
                    pass

                seen_urls.add(full_url)
                results.append(NewsItem(
                    trigger_keyword=keyword,
                    news_time=target_date if target_date else datetime.now().strftime("%Y-%m-%d"),
                    url=full_url,
                    title=text,
                    content="",
                    source=site_url,
                    tier="crawler", # Was "core"
                    score=1.0
                ))
                if len(results) >= 5:
                    break
                    
    except Exception as e:
        print(f"Tier 1 search failed for {site_url}: {e}")
        
    return results

def _search_authoritative_tier2_sync(keyword: str, domains: List[str], max_results: int, target_date: Optional[str] = None) -> List[NewsItem]:
    """
    Tier 2: Authoritative Website Search (Sync implementation for Tavily)
    """
    results = []
    
    # Append date to query if provided to bias results
    search_query = f"{keyword} {target_date}" if target_date else keyword

    tavily_results = perform_tavily_search(
        query=search_query,
        search_depth="advanced",
        include_domains=domains,
        max_results=max_results
    )
    
    for res in tavily_results:
        pub_date = res.get('published_date')
        
        results.append(NewsItem(
            trigger_keyword=keyword,
            news_time=pub_date if pub_date else (target_date if target_date else datetime.now().strftime("%Y-%m-%d")),
            url=res.get('url'),
            title=res.get('title'),
            content=res.get('content', '')[:500],
            source=res.get('url'),
            tier="tavily", # Was "authoritative"
            score=0.8
        ))
            
    return results

async def _search_global_tier3(keyword: str, max_results: int, target_date: Optional[str] = None) -> List[NewsItem]:
    """
    Tier 3: Global Internet Search
    Strategy: Use Alibaba API
    """
    results = []
    try:
        search_query = f"{keyword} {target_date}" if target_date else keyword
        search_res = await perform_search(query=search_query)
        
        if search_res.success and search_res.data:
            body = search_res.data.get('body', {})
            items = body.get('data', {}).get('results', [])
            
            for item in items:
                title = item.get('title', '')
                content = item.get('content', '')
                
                # Strict filtering
                if keyword not in title and keyword not in content:
                    continue
                
                results.append(NewsItem(
                    trigger_keyword=keyword,
                    news_time=target_date if target_date else datetime.now().strftime("%Y-%m-%d"),
                    url=item.get('url'),
                    title=title,
                    content=content[:500],
                    source="global_search",
                    tier="aliyun", # Was "global"
                    score=0.5
                ))
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"Tier 3 search failed: {e}")
        
    return results

async def search_news(request: NewsSearchRequest) -> NewsSearchResponse:
    """
    Intelligence Aggregation and Summarization System
    """
    print(f"[DEBUG] search_news called with keywords: {request.keywords}")
    all_results = []
    
    # 1. Tier 1: Core Gov Sites
    if request.gov_sites:
        print(f"[DEBUG] Starting Tier 1 search on: {request.gov_sites}")
        async with aiohttp.ClientSession() as session:
            for keyword in request.keywords:
                for site in request.gov_sites:
                    res = await _search_gov_site_tier1(session, site, keyword, request.target_date)
                    print(f"[DEBUG] Tier 1 {site} result count: {len(res)}")
                    all_results.extend(res)

    # 2. Tier 2: Authoritative Sites (Tavily)
    if request.authoritative_sites:
        print(f"[DEBUG] Starting Tier 2 (Tavily) search")
        loop = asyncio.get_event_loop()
        for keyword in request.keywords:
            res = await loop.run_in_executor(
                None, 
                _search_authoritative_tier2_sync,
                keyword, 
                request.authoritative_sites, 
                request.max_results,
                request.target_date
            )
            print(f"[DEBUG] Tier 2 result count for '{keyword}': {len(res)}")
            all_results.extend(res)
    
    # 3. Tier 3: Global Search
    print(f"[DEBUG] Starting Tier 3 (Global/Alibaba) search")
    for keyword in request.keywords:
        res = await _search_global_tier3(keyword, request.max_results, request.target_date)
        print(f"[DEBUG] Tier 3 result count for '{keyword}': {len(res)}")
        all_results.extend(res)

    print(f"[DEBUG] Total raw results: {len(all_results)}")

    # Fallback: If no results found and keys are missing, add a warning item
    if not all_results:
        # Check environment variables via settings
        has_aliyun = settings.ALIBABA_CLOUD_BEARER_TOKEN or settings.ALIYUN_ACCESS_KEY_ID
        has_tavily = settings.TAVILY_API_KEY
        
        if not has_aliyun and not has_tavily:
            all_results.append(NewsItem(
                trigger_keyword="System",
                news_time=datetime.now().strftime("%Y-%m-%d"),
                url="#",
                title="⚠️ 未配置搜索 API Key",
                content="系统检测到您未配置 ALIBABA_CLOUD_BEARER_TOKEN (阿里云) 或 TAVILY_API_KEY (Tavily)。\n\n为了使用全网实时搜索功能，请在 backend/.env 文件中配置这些密钥。\n\n当前仅尝试了有限的静态爬虫 (Tier 1)，但目标网站 (如 gov.cn) 可能存在反爬策略或动态加载导致无结果。",
                source="System Notification",
                tier="core",
                score=10.0
            ))

    # De-duplication and Sorting
    seen_urls = set()
    unique_results = []
    for item in all_results:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique_results.append(item)
    
    unique_results.sort(key=lambda x: x.score, reverse=True)
    final_results = unique_results[:request.max_results]
    
    return NewsSearchResponse(
        success=True,
        data={
            "results": [item.dict() for item in final_results],
            "count": len(final_results),
            "breakdown": {
                "tier1_core": len([i for i in final_results if i.tier == "core"]),
                "tier2_auth": len([i for i in final_results if i.tier == "authoritative"]),
                "tier3_global": len([i for i in final_results if i.tier == "global"])
            }
        },
        message=f"Aggregated {len(final_results)} items from 3 tiers"
    )

class NewsQueryExecutor:
    """
    Custom News Query Executor
    """
    
    def __init__(self, keywords: list, group_tag: str, keyword_constraints: str, result_requirements: str, time_range: str = None, max_char_limit: int = 500, enabled_tiers: List[str] = ["crawler", "tavily", "aliyun"]):
        self.keywords = keywords
        self.group_tag = group_tag
        self.keyword_constraints = keyword_constraints
        self.result_requirements = result_requirements
        self.time_range = time_range
        self.max_char_limit = max_char_limit
        self.enabled_tiers = enabled_tiers

    def construct_query(self, keyword: str) -> str:
        base_query = f"在中文新闻网站中搜索{self.group_tag}关于{keyword}"
        
        if self.keyword_constraints:
            query = f"{base_query}的{self.keyword_constraints}"
        else:
            query = f"{base_query}相关内容"
        
        if self.time_range:
            query += f"，时间限定在{self.time_range}"
            
        if self.result_requirements:
            query += f"，{self.result_requirements}"
            
        return query

    def extract_date_from_url(self, url: str) -> Optional[str]:
        if not url:
            return None
            
        patterns = [
            r'/(\d{4})/(\d{1,2})/(\d{1,2})/',  # /2023/01/01/
            r'/(\d{4})-(\d{1,2})-(\d{1,2})/',  # /2023-01-01/
            r'/t(\d{4})(\d{2})(\d{2})_',       # /t20230101_
            r'/(\d{4})(\d{2})(\d{2})/',        # /20230101/
            r'(\d{4})-(\d{1,2})-(\d{1,2})',    # 2023-01-01
        ]
        
        for p in patterns:
            match = re.search(p, url)
            if match:
                return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
        return None

    async def _fetch_page_date(self, url: str) -> Optional[str]:
        if not url:
            return None
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=5, ssl=False) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                
                if "_$jsvmprt" in html or "TAC.sign" in html:
                    return None
                
                date_patterns = [
                    r"发布时间[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)",
                    r"发布日期[:：]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)",
                    r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)\s*\d{2}:\d{2}", 
                ]
                
                for p in date_patterns:
                    match = re.search(p, html)
                    if match:
                        d = match.group(1)
                        return d.replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').replace('.', '-')
                        
                soup = BeautifulSoup(html, 'html.parser')
                meta_date = soup.find('meta', {'property': 'article:published_time'}) or \
                            soup.find('meta', {'name': 'pubdate'}) or \
                            soup.find('meta', {'name': 'publishdate'})
                
                if meta_date:
                    d = meta_date.get('content')
                    if d:
                        match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", d)
                        if match:
                            return match.group(1)
                        return d

        except Exception as e:
            pass
            
        return None

    async def extract_title_and_date(self, content: str, url: str = None):
        if not content:
            content = ""
            
        lines = content.strip().split('\n')
        title = lines[0].strip() if lines else "Unknown Title"
        
        news_time = "Unknown"
        
        date_pattern = r"(\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2}日?)"
        match = re.search(date_pattern, content)
        if match:
            date_str = match.group(1)
            date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').replace('.', '-')
            news_time = date_str
        
        if news_time == "Unknown" and url:
            url_date = self.extract_date_from_url(url)
            if url_date:
                news_time = url_date
        
        if news_time == "Unknown" and url:
             fetched_date = await self._fetch_page_date(url)
             if fetched_date:
                 news_time = fetched_date
        
        return title, news_time

    async def execute(self) -> List[NewsItem]:
        total_results = []
        seen_urls = set()
        
        for keyword in self.keywords:
            # 1. Aliyun Search (Tier 3)
            if 'aliyun' in self.enabled_tiers:
                query = self.construct_query(keyword)
                print(f"[DEBUG] Executing custom query (Aliyun): {query}")
                
                response = await perform_search(query=query)
                
                if response.success:
                    try:
                        body = response.data.get('body', {})
                        data = body.get('data', {})
                        result_wrapper = body.get('result', {})
                            
                        results = result_wrapper.get('search_result', []) if result_wrapper else []
                        if not results:
                            results = data.get('results', [])

                        for item in results:
                            if not isinstance(item, dict):
                                try:
                                    item = item.to_map()
                                except:
                                    try:
                                        item = vars(item)
                                    except:
                                        pass
                            
                            url = item.get('link') or item.get('url')
                            content = item.get('content') or item.get('snippet') or ''
                            
                            title, news_time = await self.extract_title_and_date(content, url)
                            
                            if item.get('title'):
                                title = item.get('title')
                                
                            if item.get('publish_time'):
                                news_time = item.get('publish_time')
                            
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                
                                source = "alibaba_web_search"
                                try:
                                    if url:
                                        parsed_uri = urlparse(url)
                                        source = parsed_uri.netloc
                                except:
                                    pass
                                
                                if item.get('siteName'):
                                    source = item.get('siteName')
                                elif item.get('site'):
                                    source = item.get('site')

                                news_item = NewsItem(
                                    trigger_keyword=keyword,
                                    news_time=news_time,
                                    url=url,
                                    title=title,
                                    content=content[:500],
                                    source=source,
                                    tier="aliyun", # Was "global"
                                    score=1.0
                                )
                                total_results.append(news_item)
                                
                    except Exception as e:
                        print(f"Error parsing Aliyun results for {keyword}: {e}")

            # 2. Tavily Search (Tier 2)
            if 'tavily' in self.enabled_tiers:
                try:
                    # For Tavily, use constructed query to maintain context
                    query = self.construct_query(keyword)
                    loop = asyncio.get_event_loop()
                    tavily_res = await loop.run_in_executor(
                        None, 
                        perform_tavily_search,
                        query, 
                        "advanced",
                        None,
                        10 # limit
                    )
                    
                    print(f"[DEBUG] Tavily custom search found {len(tavily_res)} results for query: {query}")
                    
                    for res in tavily_res:
                        url = res.get('url')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            
                            total_results.append(NewsItem(
                                trigger_keyword=keyword,
                                news_time=res.get('published_date', datetime.now().strftime("%Y-%m-%d")),
                                url=url,
                                title=res.get('title'),
                                content=res.get('content', '')[:500],
                                source=urlparse(url).netloc if url else "tavily_search",
                                tier="tavily", # Was "authoritative"
                                score=0.9
                            ))
                except Exception as e:
                    print(f"Error executing Tavily custom search: {e}")

            # 3. Crawler Search (Tier 1)
            if 'crawler' in self.enabled_tiers:
                try:
                    default_gov_sites = ["gov.cn", "miit.gov.cn"]
                    async with aiohttp.ClientSession() as session:
                        for site in default_gov_sites:
                            # Use keyword directly for crawler, not the long query string
                            crawler_res = await _search_gov_site_tier1(session, site, keyword, self.time_range) # time_range might act as target_date filter
                            print(f"[DEBUG] Crawler custom search found {len(crawler_res)} results for {site}")
                            
                            for item in crawler_res:
                                if item.url and item.url not in seen_urls:
                                    seen_urls.add(item.url)
                                    item.tier = "crawler"
                                    total_results.append(item)
                except Exception as e:
                    print(f"Error executing Crawler custom search: {e}")
        
        return total_results

    async def execute_stream(self):
        """
        Stream results as they are found
        """
        seen_urls = set()
        
        for keyword in self.keywords:
            query = self.construct_query(keyword)
            
            try:
                response = await perform_search(query=query)
                
                if response.success:
                    try:
                        body = response.data.get('body', {})
                        data = body.get('data', {})
                        result_wrapper = body.get('result', {})
                        
                        results = result_wrapper.get('search_result', []) if result_wrapper else []
                        if not results:
                            results = data.get('results', [])

                        keyword_results = []
                        for item in results:
                            if not isinstance(item, dict):
                                try:
                                    item = item.to_map()
                                except:
                                    try:
                                        item = vars(item)
                                    except:
                                        continue
                            
                            url = item.get('link') or item.get('url')
                            content = item.get('content') or item.get('snippet') or ''
                            
                            title, news_time = await self.extract_title_and_date(content, url)
                            
                            if item.get('title'):
                                raw_title = item.get('title').strip()
                                if raw_title and raw_title not in ["新闻", "首页", "Home", "News", "无标题", "Unknown"]:
                                    title = raw_title
                                else:
                                    if content:
                                        first_sentence = re.split(r'[。！？\n]', content)[0]
                                        title = first_sentence[:30] + "..." if len(first_sentence) > 30 else first_sentence
                            
                            if item.get('publish_time'):
                                news_time = item.get('publish_time')
                            
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                
                                source = "alibaba_web_search"
                                try:
                                    if url:
                                        parsed_uri = urlparse(url)
                                        source = parsed_uri.netloc
                                except:
                                    pass
                                
                                if item.get('siteName'):
                                    source = item.get('siteName')
                                elif item.get('site'):
                                    source = item.get('site')

                                news_item = NewsItem(
                                    trigger_keyword=keyword,
                                    news_time=news_time,
                                    url=url,
                                    title=title,
                                    content=content[:500],
                                    source=source,
                                    tier="aliyun", # Was "global"
                                    score=1.0
                                )
                                keyword_results.append(news_item)
                        
                        if keyword_results:
                            yield keyword_results
                            
                    except Exception as e:
                        print(f"Error parsing results for {keyword}: {e}")
            except Exception as e:
                print(f"Search error for {keyword}: {e}")

async def execute_custom_news_search_stream(request: CustomNewsSearchRequest):
    executor = NewsQueryExecutor(
        keywords=request.keywords,
        group_tag=request.group_tag,
        keyword_constraints=request.keyword_constraints,
        result_requirements=request.result_requirements,
        time_range=request.time_range,
        max_char_limit=request.max_char_limit,
        enabled_tiers=request.enabled_tiers
    )
    
    async for batch in executor.execute_stream():
        for item in batch:
            yield json.dumps(item.dict(), ensure_ascii=False) + "\n"

async def execute_custom_news_search(request: CustomNewsSearchRequest) -> NewsSearchResponse:
    print(f"[DEBUG] custom_search called with keywords: {request.keywords}, group: {request.group_tag}")
    executor = NewsQueryExecutor(
        keywords=request.keywords,
        group_tag=request.group_tag,
        keyword_constraints=request.keyword_constraints,
        result_requirements=request.result_requirements,
        time_range=request.time_range,
        max_char_limit=request.max_char_limit
    )
    
    results = await executor.execute()
    print(f"[DEBUG] custom_search raw result count: {len(results)}")
    
    if not results:
        # Note: Custom search relies on Alibaba Cloud Search and Tavily
        has_aliyun = settings.ALIBABA_CLOUD_BEARER_TOKEN
        has_tavily = settings.TAVILY_API_KEY
        
        if not has_aliyun and not has_tavily:
            results.append(NewsItem(
                trigger_keyword="System",
                news_time=datetime.now().strftime("%Y-%m-%d"),
                url="#",
                title="⚠️ 未配置搜索 API Key",
                content="高级自定义搜索依赖于阿里云网络搜索或 Tavily 服务。\n请在 backend/.env 文件中配置 ALIBABA_CLOUD_BEARER_TOKEN 或 TAVILY_API_KEY。\n\n如果没有这些 Key，无法执行搜索。",
                source="System Notification",
                tier="core",
                score=10.0
            ))

    return NewsSearchResponse(
        success=True,
        data={
            "results": [item.dict() for item in results],
            "count": len(results)
        },
        message=f"Found {len(results)} items"
    )
