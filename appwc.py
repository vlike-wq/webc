import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import io

# --- Page Setup ---
st.set_page_config(page_title="Pro Scraper & File Intelligence", page_icon="🛡️", layout="wide")

def analyze_file_info(file_bytes):
    """
    Returns a list of dictionaries containing detailed file metadata.
    Matches the user's expected format (File Type, MIME, Extension).
    """
    try:
        # Get all possible matches
        matches = puremagic.from_string(file_bytes)
        
        if not matches:
            return None
            
        results = []
        for m in matches:
            results.append({
                "File Type": m.name,
                "MIME Type": m.mime,
                "Suggested Extension": m.extension
            })
        return results
    except Exception as e:
        return f"Error: {str(e)}"

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Source Analyzer")
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    
    if st.button("Analyze Website"):
        with st.spinner("Probing server..."):
            try:
                res = chatter_requests.get(source_url, impersonate="chrome120", timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Status", res.status_code)
                c2.metric("Protocol", "HTTPS" if source_url.startswith("https") else "HTTP")
                
                # Logic to guess JS requirement
                scripts = len(soup.find_all('script'))
                links = len(soup.find_all('a'))
                js_req = "High" if scripts > 15 and links < 20 else "Low"
                c3.metric("JS Dependency", js_req)
                
                st.divider()
                st.subheader("Technical Strategy")
                if res.status_code == 200:
                    st.success("✅ TLS Bypass Successful. Use `curl_cffi` for this source.")
                else:
                    st.error(f"❌ Access Denied (Status {res.status_code}).")
                    
            except Exception as e:
                st.error(f"Connection Error: {e}")

elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    st.info("Identify files by their binary signatures (Magic Numbers).")
    
    tab1, tab2 = st.tabs(["Analyze via URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Direct File URL:")
        if st.button("Inspect Remote"):
            if file_url:
                with st.spinner("Downloading header..."):
                    try:
                        # Fetch first 2KB only
                        resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-2048"}, timeout=10)
                        data = analyze_file_info(resp.content)
                        if data:
                            for item in data:
                                st.write(f"**File Type:** {item['File Type']}")
                                st.write(f"**MIME Type:** `{item['MIME Type']}`")
                                st.write(f"**Suggested extension(s):** `{item['Suggested Extension']}`")
                                st.markdown("---")
                        else:
                            st.error("Could not identify file type from URL content.")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

    with tab2:
        uploaded_file = st.file_uploader("Upload a file for deep analysis", type=None)
        if uploaded_file:
            # Use getvalue() to avoid stream exhaustion
            file_bytes = uploaded_file.getvalue()
            
            if st.button("Run Deep Scan"):
                with st.spinner("Analyzing bytes..."):
                    results = analyze_file_info(file_bytes)
                    
                    if results:
                        st.success(f"Identity confirmed for: {uploaded_file.name}")
                        
                        # Display the top match prominently
                        top = results[0]
                        st.markdown(f"### **Primary Match**")
                        st.write(f"**File Type:** {top['File Type']}")
                        st.write(f"**MIME Type:** `{top['MIME Type']}`")
                        st.write(f"**Suggested extension(s):** `{top['Suggested Extension']}`")
                        
                        if len(results) > 1:
                            with st.expander("View secondary matches (nested types)"):
                                st.table(pd.DataFrame(results[1:]))
                    else:
                        st.warning("⚠️ **No Magic Numbers Detected.**")
                        st.info("This file appears to be **Plain Text (ASCII/UTF-8)**. Text files (like .txt, .csv, .json) do not have binary headers and are identified by content rather than signatures.")
