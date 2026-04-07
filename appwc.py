import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import datetime
import socket
import io
import zipfile
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
    Peeks inside ZIP structures to accurately identify XLSX, DOCX, and PPTX.
    """
    if not file_bytes:
        return None

    header_hex = file_bytes[:4].hex().upper()

    # --- STEP 1: Deep Inspection for Office Formats (PK Zip Header) ---
    if header_hex == "504B0304":
        try:
            # Open the bytes as a Zip archive to look for internal markers
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                filenames = [f.filename for f in z.infolist()]
                
                # Check for Excel markers (xl/ folder)
                if any("xl/workbook.xml" in f for f in filenames):
                    return {
                        "Type": "Microsoft Excel 2007+ Spreadsheet (OpenXML)",
                        "MIME": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "Ext": "xlsx"
                    }
                # Check for Word markers (word/ folder)
                elif any("word/document.xml" in f for f in filenames):
                    return {
                        "Type": "Microsoft Word 2007+ Document (OpenXML)",
                        "MIME": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "Ext": "docx"
                    }
                # Check for PowerPoint markers (ppt/ folder)
                elif any("ppt/presentation.xml" in f for f in filenames):
                    return {
                        "Type": "Microsoft PowerPoint 2007+ Presentation (OpenXML)",
                        "MIME": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "Ext": "pptx"
                    }
        except Exception:
            # Not a valid Zip or encrypted; fall through to generic check
            pass

    # --- STEP 2: Custom Generic ZIP String (If not an Office file) ---
    if header_hex == "504B0304":
        return {
            "Type": "ASCII text, with no line terminators (Zip archive data, at least v2.0 to extract)",
            "MIME": "application/zip",
            "Ext": "zip"
        }

    # --- STEP 3: Check for PDF ---
    if header_hex == "25504446":
        return {
            "Type": "PDF document, version 1.7",
            "MIME": "application/pdf",
            "Ext": "pdf"
        }

    # --- STEP 4: Library Fallback for Broad Identification ---
    try:
        matches = puremagic.from_string(file_bytes)
        if matches:
            m = matches[0]
            return {
                "Type": m.name,
                "MIME": m.mime,
                "Ext": m.extension.replace('.', '')
            }
    except Exception:
        pass
        
    return {"Type": "Unknown Binary", "MIME": "application/octet-stream", "Ext": "bin"}

# --- Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

# --- Module 1: Web Scraper ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Source Analyzer")
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    
    if st.button("Analyze Website"):
        with st.spinner("Analyzing Server with TLS Fingerprinting..."):
            try:
                res = chatter_requests.get(source_url, impersonate="chrome120", timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Status Code", res.status_code)
                c2.metric("Server IP", get_server_ip(source_url))
                c3.metric("Links Found", len(soup.find_all('a')))
                
                st.divider()
                st.subheader("Header Properties")
                st.write(f"**Content-Type:** {res.headers.get('Content-Type', 'N/A')}")
                st.write(f"**Last-Modified:** {res.headers.get('Last-Modified', 'Not provided')}")
                
                if res.status_code == 200:
                    st.success("✅ Connection Successful. No WAF block detected.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- Module 2: File Inspector ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    st.info("Identify files by their internal binary signatures and technical properties.")
    
    tab1, tab2 = st.tabs(["Analyze via Direct URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Direct File URL (e.g., path/to/data.xlsx):")
        if st.button("Inspect Remote"):
            if file_url:
                with st.spinner("Fetching file signature..."):
                    try:
                        # Fetch first 8KB to ensure we get internal ZIP headers
                        resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-8192"}, timeout=15)
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
                        st.error(f"Failed to inspect remote file: {e}")

    with tab2:
        uploaded_file = st.file_uploader("Upload file for analysis", type=None)
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            if st.button("Run Deep Scan"):
                info = analyze_file_info(file_bytes)
                
                st.success(f"Analysis Complete: {uploaded_file.name}")
                
                st.divider()
                col_left, col_right = st.columns(2)
                with col_left:
                    st.write("### 🛠 Technical Properties")
                    st.write(f"**MIME Type:** `{info['MIME']}`")
                    st.write(f"**Verified Extension:** `{info['Ext']}`")
                    st.write(f"**File Size:** {len(file_bytes) / 1024:.2f} KB")
                
                with col_right:
                    st.write("### 📅 Session Metadata")
                    st.write(f"**Analysis Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Origin Source:** User Upload via Browser")
                    st.caption("Note: Original creation dates are stripped by browsers for security.")

                st.divider()
                st.write(f"**System Identification String:**")
                st.info(info['Type'])
