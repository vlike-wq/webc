import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Page Configuration
st.set_page_config(
    page_title="Pro Web Scraper Analyzer",
    page_icon="🛡️",
    layout="wide"
)

def analyze_url(url):
    """
    Performs a high-level analysis using TLS Impersonation to bypass WAFs.
    """
    results = {}
    
    try:
        # We use 'impersonate="chrome120"' to mimic a real browser's TLS handshake
        # This is much stronger than just changing the User-Agent string.
        response = chatter_requests.get(
            url, 
            impersonate="chrome120", 
            timeout=30, 
            allow_redirects=True
        )
        
        results['status_code'] = response.status_code
        results['url_reached'] = response.url
        results['connection_type'] = "HTTPS (Secure)" if response.url.startswith("https") else "HTTP (Unsecure)"
        results['content_type'] = response.headers.get('Content-Type', 'Unknown').split(';')[0]
        
        # Check for "Soft Blocks" (200 OK but shows Access Denied text)
        is_blocked = "Access Denied" in response.text or response.status_code in [403, 401]
        results['is_blocked'] = is_blocked
        
        # DOM Analysis
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        links = soup.find_all('a')
        
        results['script_count'] = len(scripts)
        results['link_count'] = len(links)
        
        # Logic for Feedback
        if is_blocked:
            results['js_required'] = "Unknown (Blocked)"
            results['strategy'] = "Critical: IP or Fingerprint flagged. Use Residential Proxies."
            results['color'] = "error"
        elif results['link_count'] < 5 and results['script_count'] > 10:
            results['js_required'] = "Yes (SPA Detected)"
            results['strategy'] = "Medium: Content is likely hidden behind JS. Use Playwright/Puppeteer."
            results['color'] = "warning"
        else:
            results['js_required'] = "No (Static HTML)"
            results['strategy'] = "Success: Site is accessible. Standard scraping (BeautifulSoup) will work."
            results['color'] = "success"

        results['raw_content'] = response.text
        results['headers'] = dict(response.headers)
        return results, None

    except Exception as e:
        return None, f"Connection Failed: {str(e)}"

# --- UI Layout ---
st.title("🛡️ Pro Scraper Analyzer (WAF Bypass Edition)")
st.markdown("This version uses **TLS Fingerprint Impersonation** to analyze sites protected by Akamai, Cloudflare, or Datadome.")

# Default to your problematic URL for testing
target_url = st.text_input("Target URL:", value="https://www.tcs.com/investor-relations/financial-statements")

if st.button("Run Stealth Analysis"):
    if target_url:
        with st.spinner('Performing Stealth Handshake...'):
            data, error = analyze_url(target_url)
            
            if error:
                st.error(error)
                st.info("Tip: If this failed, the site might be blocking your specific IP address entirely.")
            else:
                # Top Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Status Code", data['status_code'])
                m2.metric("Connection", "Secure" if "HTTPS" in data['connection_type'] else "Unsecure")
                m3.metric("JS Required", data['js_required'])
                m4.metric("Links Found", data['link_count'])

                st.divider()

                # Strategy Section
                st.subheader("🛠 Technical Strategy")
                if data['color'] == "error":
                    st.error(f"⚠️ {data['strategy']}")
                elif data['color'] == "warning":
                    st.warning(f"⚡ {data['strategy']}")
                else:
                    st.success(f"✅ {data['strategy']}")

                # Detail Columns
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("Node.js Puppeteer Script Generator"):
                        st.code(f"""
const puppeteer = require('puppeteer');

(async () => {{
  const browser = await puppeteer.launch({{ headless: true }});
  const page = await browser.newPage();
  
  // Use a realistic user agent
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...');
  
  await page.goto('{target_url}', {{ waitUntil: 'networkidle2' }});
  
  // Extract content
  const content = await page.content();
  console.log("Page Analyzed.");
  
  await browser.close();
}})();
                        """, language="javascript")

                with col2:
                    st.write("**Detected Content Type:**", data['content_type'])
                    st.write("**Scripts on Page:**", data['script_count'])
                    st.write("**Final URL:**", data['url_reached'])

                st.divider()

                # Content Tabs
                tab1, tab2 = st.tabs(["HTML Preview", "Response Headers"])
                with tab1:
                    st.code(data['raw_content'][:5000], language="html")
                with tab2:
                    st.json(data['headers'])
    else:
        st.warning("Please enter a URL.")

# Instructions
st.sidebar.header("Analyzer Logic")
st.sidebar.markdown("""
- **Level 1: Connection**
  Uses `curl_cffi` to mimic Chrome's TLS fingerprint to bypass Akamai/Cloudflare.
- **Level 2: Method**
  Determines if a direct GET request returns valid data.
- **Level 3: Requirement**
  Analyzes link-to-script ratio to determine if JavaScript execution is necessary.
""")
