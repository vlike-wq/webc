import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import io

# --- Page Setup ---
st.set_page_config(page_title="Scraper & File Intelligence", page_icon="🛡️", layout="wide")

# --- Logic Functions ---

def analyze_file_bytes(file_bytes):
    """Identifies file type using magic numbers from a byte stream."""
    try:
        results = puremagic.from_string(file_bytes)
        return results
    except puremagic.PureError:
        return "Unknown File Type"
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_url(url):
    """Performs the scraper-level analysis on a webpage."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}
    try:
        # Using curl_cffi for WAF bypass
        response = chatter_requests.get(url, impersonate="chrome120", timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        details = {
            "status": response.status_code,
            "conn": "HTTPS" if url.startswith("https") else "HTTP",
            "js_needed": "Yes" if len(soup.find_all('script')) > 15 and len(soup.find_all('a')) < 10 else "No",
            "links": soup.find_all('a'),
            "raw": response.text
        }
        return details, None
    except Exception as e:
        return None, str(e)

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

# --- Module 1: Web Scraper Analyzer ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Source Analyzer")
    st.write("Analyze a URL to determine scraping difficulty and connection details.")
    
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    
    if st.button("Analyze Website"):
        with st.spinner("Probing server..."):
            data, error = analyze_url(source_url)
            if error:
                st.error(error)
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Status", data['status'])
                c2.metric("Protocol", data['conn'])
                c3.metric("JS Likely Required", data['js_needed'])
                
                with st.expander("View Discovered Links"):
                    link_list = [a.get('href') for a in data['links'] if a.get('href')]
                    st.write(pd.DataFrame(link_list, columns=["URL"]))

# --- Module 2: Deep File Inspector ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    st.write("Verify the true identity of a file using 'Magic Number' byte analysis.")
    
    tab1, tab2 = st.tabs(["Check via Direct URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Enter Direct File URL (e.g., .pdf, .zip, .exe):")
        if st.button("Inspect Remote File"):
            if file_url:
                with st.spinner("Fetching file header..."):
                    try:
                        # Request only the first 2KB to save bandwidth
                        res = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-2048"}, timeout=10)
                        results = analyze_file_bytes(res.content)
                        
                        if isinstance(results, list):
                            st.success("File Identified Successfully!")
                            st.table(pd.DataFrame([{"Extension": r.extension, "MIME": r.mime, "Name": r.name} for r in results]))
                        else:
                            st.error(results)
                    except Exception as e:
                        st.error(f"Failed to reach file: {e}")
            else:
                st.warning("Please enter a URL.")

    with tab2:
        uploaded_file = st.file_uploader("Drag and drop a file to verify its true type", type=None)
        if uploaded_file is not None:
            with st.spinner("Analyzing uploaded bytes..."):
                file_bytes = uploaded_file.read()
                results = analyze_file_bytes(file_bytes)
                
                if isinstance(results, list):
                    st.success(f"Analysis Complete for: {uploaded_file.name}")
                    st.table(pd.DataFrame([{"True Extension": r.extension, "MIME": r.mime, "Description": r.name} for r in results]))
                    
                    # Security Check
                    actual_ext = results[0].extension.lower()
                    reported_ext = "." + uploaded_file.name.split('.')[-1].lower()
                    if actual_ext != reported_ext:
                        st.warning(f"🚨 **Spoofing Alert:** File name says {reported_ext} but internal signature is {actual_ext}!")
                else:
                    st.error("Could not identify file type.")

# --- Footer Info ---
st.sidebar.divider()
st.sidebar.caption("v2.1 | TLS Fingerprinting Active | Magic Number Inspection Active")
