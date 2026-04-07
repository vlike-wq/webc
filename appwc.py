import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import datetime
import socket
from urllib.parse import urlparse

# --- Page Setup ---
st.set_page_config(page_title="Pro Scraper & File Intelligence", page_icon="🛡️", layout="wide")

def get_server_ip(url):
    """Extracts the IP address from a URL to identify Origin."""
    try:
        hostname = urlparse(url).hostname
        if hostname:
            return socket.gethostbyname(hostname)
        return "N/A"
    except:
        return "Unknown"

def analyze_file_info(file_bytes):
    """
    Advanced Identification Engine:
    Distinguishes between generic ZIPs and Office OpenXML (XLSX, DOCX, PPTX).
    """
    if not file_bytes:
        return None

    try:
        # Use puremagic for deep inspection (it looks past the first 4 bytes)
        matches = puremagic.from_string(file_bytes)
        if matches:
            m = matches[0]
            
            # 1. Check for specific Office OpenXML Mime Types first
            if "officedocument" in m.mime:
                return {
                    "Type": m.name,
                    "MIME": m.mime,
                    "Ext": m.extension.replace('.', '')
                }
            
            # 2. If it's a generic ZIP, use your specific description string
            if m.mime == "application/zip" or m.extension == ".zip":
                return {
                    "Type": "ASCII text, with no line terminators (Zip archive data, at least v2.0 to extract)",
                    "MIME": "application/zip",
                    "Ext": "zip"
                }

            # 3. Handle all other identified types
            return {
                "Type": m.name,
                "MIME": m.mime,
                "Ext": m.extension.replace('.', '')
            }
    except Exception:
        pass

    # 4. Manual Fallback for the very basics
    header_hex = file_bytes[:4].hex().upper()
    if header_hex == "504B0304":
        return {"Type": "Compressed Archive (ZIP)", "MIME": "application/zip", "Ext": "zip"}
    elif header_hex == "25504446":
        return {"Type": "PDF Document", "MIME": "application/pdf", "Ext": "pdf"}
        
    return {"Type": "Unknown Binary", "MIME": "application/octet-stream", "Ext": "bin"}

# --- Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

# --- Module 1: Web Scraper ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Source Analyzer")
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    
    if st.button("Analyze Website"):
        with st.spinner("Analyzing Server..."):
            try:
                res = chatter_requests.get(source_url, impersonate="chrome120", timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Status Code", res.status_code)
                c2.metric("Server Origin (IP)", get_server_ip(source_url))
                c3.metric("Links Found", len(soup.find_all('a')))
                
                st.divider()
                st.subheader("Connection Details")
                st.write(f"**Content-Type (Header):** {res.headers.get('Content-Type', 'N/A')}")
                st.write(f"**Last Modified (Header):** {res.headers.get('Last-Modified', 'Not provided')}")
                
                if res.status_code == 200:
                    st.success("✅ TLS Fingerprint accepted by server.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- Module 2: File Inspector ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    st.info("Identify files by their internal binary signatures and properties.")
    
    tab1, tab2 = st.tabs(["Analyze via Direct URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Direct File URL:")
        if st.button("Inspect Remote"):
            if file_url:
                with st.spinner("Fetching headers and magic numbers..."):
                    try:
                        # Only fetch first 4KB
                        resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-4096"}, timeout=10)
                        info = analyze_file_info(resp.content)
                        
                        st.subheader("Properties & Origin")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Origin (IP):** {get_server_ip(file_url)}")
                            st.write(f"**MIME Type:** `{info['MIME']}`")
                        with col2:
                            st.write(f"**Server Last Modified:** {resp.headers.get('Last-Modified', 'N/A')}")
                            st.write(f"**Suggested Extension:** `{info['Ext']}`")
                        
                        st.divider()
                        st.write(f"**File Type Description:**")
                        st.info(info['Type'])
                    except Exception as e:
                        st.error(f"Failed: {e}")

    with tab2:
        uploaded_file = st.file_uploader("Upload file for analysis", type=None)
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            if st.button("Run Deep Scan"):
                info = analyze_file_info(file_bytes)
                
                st.success(f"Analysis Complete: {uploaded_file.name}")
                
                st.divider()
                # Metadata Layout
                c1, c2 = st.columns(2)
                with c1:
                    st.write("### 🛠 Technical Properties")
                    st.write(f"**File Name:** {uploaded_file.name}")
                    st.write(f"**MIME Type:** `{info['MIME']}`")
                    st.write(f"**Verified Extension:** `{info['Ext']}`")
                    st.write(f"**File Size:** {len(file_bytes) / 1024:.2f} KB")
                
                with c2:
                    st.write("### 📅 Session Data")
                    st.write(f"**Analysis Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Origin:** User Upload via Browser")
                    st.caption("Note: Original creation dates are stripped by browsers for security.")

                st.divider()
                st.write(f"**Detailed Signature Identification:**")
                st.info(info['Type'])
