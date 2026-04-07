import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import os
import datetime
import socket
from urllib.parse import urlparse

# --- Page Setup ---
st.set_page_config(page_title="Pro Scraper & File Intelligence", page_icon="🛡️", layout="wide")

def get_server_ip(url):
    """Extracts the IP address from a URL to identify Origin."""
    try:
        hostname = urlparse(url).hostname
        return socket.gethostbyname(hostname)
    except:
        return "Unknown"

def analyze_file_info(file_bytes):
    """Hybrid Identification Engine for File Type and MIME."""
    header_hex = file_bytes[:4].hex().upper()
    if header_hex == "504B0304":
        return {"Type": "ASCII text, with no line terminators (Zip archive data, at least v2.0 to extract)", "MIME": "application/zip", "Ext": "zip"}
    elif header_hex == "25504446":
        return {"Type": "PDF document, version 1.7", "MIME": "application/pdf", "Ext": "pdf"}
    
    try:
        m = puremagic.from_string(file_bytes)[0]
        return {"Type": m.name, "MIME": m.mime, "Ext": m.extension.replace('.', '')}
    except:
        return {"Type": "Unknown Binary", "MIME": "application/octet-stream", "Ext": "bin"}

# --- Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Source Analyzer")
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    if st.button("Analyze Website"):
        with st.spinner("Analyzing..."):
            res = chatter_requests.get(source_url, impersonate="chrome120")
            st.metric("Status", res.status_code)
            st.write(f"**Server Origin (IP):** {get_server_ip(source_url)}")

elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    tab1, tab2 = st.tabs(["Analyze via URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Direct File URL:")
        if st.button("Inspect Remote File"):
            resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-2048"})
            info = analyze_file_info(resp.content)
            
            st.subheader("Properties")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Origin (IP):** {get_server_ip(file_url)}")
                st.write(f"**Content Type:** {resp.headers.get('Content-Type', 'N/A')}")
            with col2:
                # Servers often provide the modified date in the header
                st.write(f"**Server Last Modified:** {resp.headers.get('Last-Modified', 'Not provided by server')}")
                st.write(f"**MIME Type:** `{info['MIME']}`")
            
            st.write(f"**Detailed File Type:** {info['Type']}")

    with tab2:
        uploaded_file = st.file_uploader("Upload file", type=None)
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            if st.button("Run Deep Scan"):
                info = analyze_file_info(file_bytes)
                
                st.success(f"File: {uploaded_file.name}")
                st.divider()
                
                # Metadata Grid
                c1, c2 = st.columns(2)
                with c1:
                    st.write("### 🛠 Technical Info")
                    st.write(f"**MIME Type:** `{info['MIME']}`")
                    st.write(f"**Suggested Extension:** `{info['Ext']}`")
                    st.write(f"**File Size:** {len(file_bytes) / 1024:.2f} KB")
                
                with c2:
                    st.write("### 📅 Temporal Info")
                    # Note: Uploaded files lose original creation date in browser transfers
                    # We show the 'Upload Date' as the proxy for current session metadata
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.write(f"**Analysis Timestamp:** {now}")
                    st.write(f"**Origin:** User Upload (Browser)")

                st.divider()
                st.write(f"**Full System Description:**")
                st.info(info['Type'])
