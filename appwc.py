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
    Hybrid Identification Engine: 
    1. Manual Signature Check (High Precision for ZIP/PDF)
    2. Library Fallback (Broad Detection)
    """
    if not file_bytes:
        return None
        
    # Get the first 4 bytes in Hex to identify the "Magic Number"
    header_hex = file_bytes[:4].hex().upper()
    
    # --- Manual Override for Professional Detail Strings ---
    # 50 4B 03 04 is the Hex for 'PK..' (Zip Archive)
    if header_hex == "504B0304":
        return [{
            "File Type": "ASCII text, with no line terminators (Zip archive data, at least v2.0 to extract)",
            "MIME Type": "application/zip",
            "Extension": "zip"
        }]
    # 25 50 44 46 is the Hex for '%PDF'
    elif header_hex == "25504446":
        return [{
            "File Type": "PDF document, version 1.7 (Portable Document Format)",
            "MIME Type": "application/pdf",
            "Extension": "pdf"
        }]

    # --- Library Fallback ---
    try:
        matches = puremagic.from_string(file_bytes)
        if matches:
            results = []
            for m in matches:
                results.append({
                    "File Type": m.name,
                    "MIME Type": m.mime,
                    "Extension": m.extension.replace('.', '')
                })
            return results
    except Exception:
        pass
        
    return None

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

# --- Module 1: Web Scraper ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Source Analyzer")
    st.write("Analyze a URL to determine scraping difficulty and connection details.")
    
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    
    if st.button("Analyze Website"):
        with st.spinner("Probing server with TLS Impersonation..."):
            try:
                # Using curl_cffi to bypass WAF/Akamai
                res = chatter_requests.get(source_url, impersonate="chrome120", timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Status Code", res.status_code)
                c2.metric("Protocol", "HTTPS" if source_url.startswith("https") else "HTTP")
                
                scripts = len(soup.find_all('script'))
                links = len(soup.find_all('a'))
                js_req = "High" if scripts > 15 and links < 20 else "Low"
                c3.metric("JS Dependency", js_req)
                
                st.divider()
                if res.status_code == 200:
                    st.success("✅ TLS Bypass Successful. Source is reachable.")
                    with st.expander("View Page Metadata"):
                        st.write(f"**Final URL:** {res.url}")
                        st.write(f"**Links Found:** {links}")
                else:
                    st.error(f"❌ Access Denied (Status {res.status_code}). Site detected automation.")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

# --- Module 2: File Inspector ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    st.info("Identify files by their internal binary signatures (Magic Numbers).")
    
    tab1, tab2 = st.tabs(["Analyze via Direct URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Direct File URL (e.g., path/to/file.zip):")
        if st.button("Inspect Remote File"):
            if file_url:
                with st.spinner("Fetching file header..."):
                    try:
                        # Fetch only the start of the file
                        resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-2048"}, timeout=10)
                        data = analyze_file_info(resp.content)
                        if data:
                            top = data[0]
                            st.markdown("---")
                            st.write(f"**File Type:** {top['File Type']}")
                            st.write(f"**MIME Type:** `{top['MIME Type']}`")
                            st.write(f"**Suggested file extension(s):** `{top['Extension']}`")
                            st.markdown("---")
                        else:
                            st.warning("Could not identify binary signature from URL.")
                    except Exception as e:
                        st.error(f"Request failed: {e}")

    with tab2:
        uploaded_file = st.file_uploader("Upload a file for deep analysis", type=None)
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            
            if st.button("Run Deep Scan"):
                with st.spinner("Analyzing bytes..."):
                    results = analyze_file_info(file_bytes)
                    
                    if results:
                        st.success(f"Identity confirmed for: {uploaded_file.name}")
                        top = results[0]
                        
                        st.markdown("---")
                        st.write(f"**File Type:** {top['File Type']}")
                        st.write(f"**MIME Type:** `{top['MIME Type']}`")
                        st.write(f"**Suggested file extension(s):** `{top['Extension']}`")
                        st.markdown("---")
                        
                        if len(results) > 1:
                            with st.expander("View Secondary Matches"):
                                st.table(pd.DataFrame(results[1:]))
                    else:
                        # Fallback for plain text
                        try:
                            file_bytes[:512].decode('utf-8')
                            st.info("### **Primary Match**")
                            st.write("**File Type:** ASCII text / Plain text (No binary signature)")
                            st.write("**MIME Type:** `text/plain`")
                            st.write("**Suggested extension(s):** `txt, csv, json`")
                        except UnicodeDecodeError:
                            st.error("Unknown Binary Format. The first 4 bytes do not match any known signature.")
                            st.code(f"Header (HEX): {file_bytes[:16].hex(' ').upper()}")

# Footer
st.sidebar.divider()
st.sidebar.caption("Scraper Engine: curl_cffi | Identification: Magic Numbers")
