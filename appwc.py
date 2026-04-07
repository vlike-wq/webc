import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Advanced Web Scraper Analyzer",
    page_icon="🔍",
    layout="wide"
)

def analyze_url(url):
    """
    Performs a multi-level analysis of the target URL.
    """
    results = {}
    # Enhanced headers to mimic a real Chrome browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    try:
        # Step 1: Initial Request Analysis
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        results['status_code'] = response.status_code
        results['url_reached'] = response.url
        results['connection_type'] = "HTTPS (Secure)" if response.url.startswith("https") else "HTTP (Unsecure)"
        results['content_type'] = response.headers.get('Content-Type', 'Unknown')
        
        # Step 2: Check for WAF/Access Denied
        # Even with 200, we check if the word "Access Denied" or Akamai headers are present
        is_blocked = "Access Denied" in response.text or response.status_code in [403, 401]
        results['is_blocked'] = is_blocked
        
        # Step 3: JS Requirement Analysis
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        links = soup.find_all('a')
        iframes = soup.find_all('iframe')
        
        # Heuristic: If there's very little text/links but many scripts, JS is likely needed
        results['script_count'] = len(scripts)
        results['link_count'] = len(links)
        
        if is_blocked:
            results['js_required'] = "Unknown (Blocked)"
            results['strategy'] = "High Difficulty: Site detected the scraper. Use Playwright with Stealth or a Proxy."
        elif len(links) < 3 and len(scripts) > 5:
            results['js_required'] = "Yes (Likely)"
            results['strategy'] = "Medium Difficulty: Requires JavaScript rendering (Puppeteer/Playwright)."
        else:
            results['js_required'] = "No (Static)"
            results['strategy'] = "Low Difficulty: Can be scraped efficiently with Requests + BeautifulSoup."

        results['raw_content'] = response.text
        return results, None

    except Exception as e:
        return None, str(e)

# --- UI Layout ---
st.title("🔍 Web Scraper Analyzer & Strategy Tool")
st.markdown("""
This tool analyzes a website to determine its security level, technical stack, 
and the best method for data extraction.
""")

url_input = st.text_input("Enter the Target URL:", value="https://www.tcs.com/investor-relations/financial-statements")

if st.button("Run Multi-Level Analysis"):
    if url_input:
        with st.spinner('Probing target server...'):
            data, error = analyze_url(url_input)
            
            if error:
                st.error(f"**Connection Failed:** {error}")
            else:
                # Top Row Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Status Code", data['status_code'])
                m2.metric("Connection", "Secure" if "HTTPS" in data['connection_type'] else "Unsecure")
                m3.metric("JS Needed", data['js_required'])
                m4.metric("Links Found", data['link_count'])

                st.divider()

                # Detailed Analysis Blocks
                col_left, col_right = st.columns([1, 1])

                with col_left:
                    st.subheader("🛠 Recommended Strategy")
                    if data['is_blocked']:
                        st.error(f"⚠️ **Access Blocked:** {data['strategy']}")
                        st.warning("The server identified this request as a bot. You may need to use residential proxies or browser-fingerprint spoofing.")
                    else:
                        st.success(f"✅ **Plan:** {data['strategy']}")
                    
                    with st.expander("View Auto-Generated Navigation Script (Node.js)"):
                        st.code(f"""
// Suggested Puppeteer Snippet for this URL
const puppeteer = require('puppeteer');

(async () => {{
  const browser = await puppeteer.launch({{ headless: true }});
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0... (matching your analyzer)');
  await page.goto('{url_input}', {{ waitUntil: 'networkidle2' }});
  
  // Target your file here
  // const file = await page.$eval('selector', el => el.href);
  
  await browser.close();
}})();
                        """, language="javascript")

                with col_right:
                    st.subheader("📄 Response Metadata")
                    st.write(f"**Final URL:** {data['url_reached']}")
                    st.write(f"**Content Type:** {data['content_type']}")
                    st.write(f"**Scripts Detected:** {data['script_count']}")
                    
                st.divider()
                
                # Raw Data Tabs
                tab1, tab2 = st.tabs(["HTML Preview", "Response Headers"])
                with tab1:
                    st.code(data['raw_content'][:5000], language="html")
                with tab2:
                    st.write(data.get('raw_content', 'No headers captured'))
                    
    else:
        st.warning("Please enter a URL to begin.")

# Sidebar Instructions
st.sidebar.header("How it works")
st.sidebar.info("""
1. **Level 1 (HTTP):** Checks if the site is reachable via standard requests.
2. **Level 2 (Security):** Identifies WAFs (Akamai, Cloudflare) or Access Denied triggers.
3. **Level 3 (DOM):** Compares link density vs script density to guess if JS rendering is mandatory.
""")
