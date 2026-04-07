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
    Returns a list of objects containing detailed file metadata.
    Accesses attributes directly to avoid TypeErrors.
    """
    try:
        # Get all possible matches
        matches = puremagic.from_string(file_bytes)
        
        if not matches:
            return None
            
        results = []
        for m in matches:
            # We create a dictionary here to standardize the output
            results.append({
                "File Type": m.name,      # e.g., "Zip archive data, at least v2.0 to extract"
                "MIME Type": m.mime,      # e.g., "application/zip"
                "Extension": m.extension  # e.g., ".zip"
            })
        return results
    except Exception as e:
        return None

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
                st.success(f"Successfully reached {source_url} (Status: {res.status_code})")
                st.write(f"**Links Found:** {len(soup.find_all('a'))}")
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
                        resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-2048"}, timeout=10)
                        data = analyze_file_info(resp.content)
                        if data:
                            top = data[0]
                            st.write(f"**File Type:** {top['File Type']}")
                            st.write(f"**MIME Type:** `{top['MIME Type']}`")
                            st.write(f"**Suggested extension(s):** `{top['Extension']}`")
                        else:
                            st.warning("Could not identify binary signature. This might be a plain text file.")
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
                        st.markdown("### **Primary Match**")
                        st.write(f"**File Type:** {top['File Type']}")
                        st.write(f"**MIME Type:** `{top['MIME Type']}`")
                        st.write(f"**Suggested extension(s):** `{top['Extension']}`")
                    else:
                        # NEW: Enhanced Fallback Logic
                        st.warning("⚠️ **No Magic Numbers Detected in Database.**")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info("### **Byte Analysis**")
                            # Show the Hexadecimal signature (The first 16 bytes)
                            hex_signature = " ".join([f"{b:02X}" for b in file_bytes[:16]])
                            st.write(f"**First 16 Bytes (HEX):**")
                            st.code(hex_signature)
                        
                        with col2:
                            # Try to see if it's readable text
                            try:
                                text_sample = file_bytes[:512].decode('utf-8')
                                st.write("**Content Inference:** ASCII / UTF-8 Text")
                                st.write("**Suggested Extension:** `.txt`, `.csv`, `.json`, `.log`")
                                with st.expander("View Text Preview"):
                                    st.text(text_sample)
                            except UnicodeDecodeError:
                                st.write("**Content Inference:** Unknown Binary / Encrypted Data")
                                st.write("**Suggested Action:** Check if the file is compressed or encrypted.")

                        # Professional "File" command style output for unknown files
                        st.divider()
                        st.write("**Detailed Diagnostic:**")
                        size_kb = len(file_bytes) / 1024
                        st.text(f"Data; {size_kb:.2f} KB; No standard signature found at offset 0.")
