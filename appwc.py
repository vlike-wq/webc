import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Page Config
st.set_page_config(page_title="Web Scraper Analyzer", layout="wide")

## --- Logic Functions ---

def analyze_url(url):
    results = {}
    try:
        # 1. Connection Analysis
        response = requests.get(url, timeout=10)
        results['status_code'] = response.status_code
        results['connection_type'] = "HTTPS (Secure)" if url.startswith("https") else "HTTP (Unsecure)"
        results['headers'] = response.headers
        
        # 2. Method Analysis
        # Checking if 'Allow' header suggests methods, otherwise defaulting to GET/POST logic
        results['method_suggestion'] = "GET" if response.request.method == "GET" else "POST"
        
        # 3. JavaScript Dependency Check
        # If the 'body' is nearly empty or contains specific JS-only tags, JS is likely required
        soup = BeautifulSoup(response.text, 'html.parser')
        links_found = len(soup.find_all('a'))
        scripts_found = len(soup.find_all('script'))
        
        # Simple heuristic: high script-to-link ratio often implies a JS-heavy app
        results['js_required'] = "Yes (Likely)" if links_found < 5 and scripts_found > 0 else "No (Static HTML)"
        results['raw_html'] = response.text[:2000] # Snippet for preview
        
        return results, None
    except Exception as e:
        return None, str(e)

## --- UI Layout ---

st.title("🔍 Multi-Level Scraper Analyzer")
st.write("Analyze a URL to determine the best scraping strategy.")

url_input = st.text_input("Enter Source URL:", placeholder="https://example.com/data")

if st.button("Run Analysis"):
    if url_input:
        with st.spinner('Analyzing source...'):
            data, error = analyze_url(url_input)
            
            if error:
                st.error(f"Error connecting to site: {error}")
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Connection", data['connection_type'])
                    st.write("**Status Code:**", data['status_code'])
                
                with col2:
                    st.metric("JS Required", data['js_required'])
                    st.write("**Preferred Method:**", data['method_suggestion'])
                
                with col3:
                    st.metric("Content Type", data['headers'].get('Content-Type', 'Unknown').split(';')[0])

                st.divider()

                # Feedback & Technical Details
                st.subheader("Technical Feedback")
                tabs = st.tabs(["Strategy", "Headers", "HTML Snippet"])
                
                with tabs[0]:
                    if data['js_required'] == "Yes (Likely)":
                        st.info("💡 **Strategy:** Use **Puppeteer** or **Playwright**. The content is likely rendered dynamically.")
                    else:
                        st.success("💡 **Strategy:** Use **Requests + BeautifulSoup**. The site is static and fast to scrape.")
                
                with tabs[1]:
                    st.json(dict(data['headers']))
                    
                with tabs[2]:
                    st.code(data['raw_html'], language="html")
    else:
        st.warning("Please enter a URL first.")
