import os
import threading
from ddgs import DDGS
import requests
import json
import time
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io

def log_pid(msg):
    print(msg, flush=True)

class ResearchAgent:
    def __init__(self, ai_strategy, db):
        self.ai = ai_strategy
        self.db = db
        self.ddgs = DDGS()
        self.stop_event = threading.Event()
        self.thread = None
        self.bypass_domains = ["binance.com", "coinbase.com", "kraken.com", "okx.com", "bybit.com", "kucoin.com", "gate.io"]

    def start_background_research(self, interval_seconds=3600):
        """Starts the research agent in a separate background thread."""
        if self.thread and self.thread.is_alive():
            return
        
        self.thread = threading.Thread(target=self._research_loop, args=(interval_seconds,), daemon=True)
        self.thread.start()
        log_pid("Permanent Background Research Agent started.")

    def _research_loop(self, interval):
        while not self.stop_event.is_set():
            try:
                self.conduct_study_session()
            except Exception as e:
                log_pid(f"Background Research Error: {e}")
            
            # Wait for interval or stop signal
            self.stop_event.wait(interval)

    def _scrape_full_content(self, url):
        """Fetches and extracts clean text from a URL."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, and junk
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            text = soup.get_text(separator=' ', strip=True)
            return text
        except Exception as e:
            # log_pid(f"Scraping error for {url}: {e}")
            return None

    def _parse_pdf(self, url):
        """Downloads a PDF and extracts its text content."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            with io.BytesIO(response.content) as pdf_file:
                reader = PdfReader(pdf_file)
                text = ""
                # Limit to first 15 pages to stay within manageable context
                for page in reader.pages[:15]:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            # log_pid(f"PDF Parsing error for {url}: {e}")
            return None

    def conduct_study_session(self):
        """Perform a research cycle to find and ingest high-standard trading expertise."""
        # Step A: Generate Dynamic Queries via AI
        log_pid("Identifying knowledge gaps for research...")
        queries = self.ai.generate_research_queries()
        
        # Fallback if AI fails: Use high-level quant topics
        if not queries:
            queries = [
                "vectorized python backtesting mean reversion github",
                "mathematical kelly criterion position sizing whitepaper .pdf",
                "hft order flow imbalance statistical analysis",
                "machine learning crypto price prediction technical guide",
                "volatility clustering arch garch models python"
            ]
        
        log_pid(f"Starting Autonomous Research Study Session with {len(queries)} technical queries...")
        all_insights = []
        
        for query in queries:
            if self.stop_event.is_set(): break
            try:
                # Extra sleep to be very respectful of DuckDuckGo rate limits
                time.sleep(5)
                log_pid(f"Searching for: {query}")
                
                # Fetch results
                results = list(self.ddgs.text(query, max_results=10))
                log_pid(f"  > Found {len(results)} potential expert sources.")
                
                if not results:
                    log_pid(f"  ! No results found for query. Possible rate limit or niche topic.")
                    continue

                for res in results:
                    title = res.get('title')
                    snippet = res.get('body')
                    href = res.get('href')
                    
                    if not href: continue

                    # Skip landing pages/exchanges
                    if any(domain in href for domain in self.bypass_domains):
                        # log_pid(f"    - Skipping known exchange/landing page: {href}")
                        continue

                    # Step B: Check for duplication via Postgres
                    if self.db.is_url_researched(href):
                        continue
                    
                    # Register immediately
                    self.db.register_researched_url(href)

                    log_pid(f"Analyzing expert source: {title}")
                    
                    # Phase 17 & 18: Deep Scrape or PDF Parse
                    content_to_analyze = None
                    if href.lower().endswith(".pdf"):
                        log_pid(f"    [PDF] Parsing document: {href}")
                        content_to_analyze = self._parse_pdf(href)
                    else:
                        full_text = self._scrape_full_content(href)
                        content_to_analyze = full_text if (full_text and len(full_text) > 800) else snippet
                    
                    if not content_to_analyze or len(content_to_analyze) < 200:
                        log_pid(f"    - Skipping: Insufficient content found.")
                        continue

                    insight = self.ai.summarize_expertise(title, content_to_analyze, href)
                    if insight and insight.lower() != "null" and "optional" not in insight.lower():
                        log_pid(f"    + SUCCESS: Distilled new high-standard rule.")
                        all_insights.append(insight)
                        # To avoid spamming, we ingest only the best 1 per query
                        break 
                    else:
                        log_pid(f"    - Result was generic or failed distillation.")
                
                time.sleep(8) # Respectful rate limiting for aggressive mode
            except Exception as e:
                log_pid(f"Search error for '{query}': {e}")

        if all_insights:
            log_pid(f"Research complete. Ingesting {len(all_insights)} new professional rules.")
            for insight in all_insights:
                self.ai.update_knowledge_base(insight)
            return True
        
        log_pid("Study session complete. No new high-standard insights found in this cycle.")
        return False
