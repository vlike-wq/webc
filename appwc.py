import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import socket
import io
import zipfile
import json
from urllib.parse import urlparse

# --- Page Setup ---
st.set_page_config(page_title="Pro Scraper, File & JSON Suite", page_icon="🛡️", layout="wide")

# --- Global Logic Functions ---

def detect_tech_stack(headers, html):
    """Identifies hosting, language, and bot detection signatures."""
    tech = {"Hosting/WAF": "Unknown", "Language/Framework": "Not Disclosed", "Bot Protection": "None Detected"}
    header_str = str(headers).lower()
    html_low = html.lower()

    if "cloudflare" in header_str or "cf-ray" in header_str:
        tech["Hosting/WAF"], tech["Bot Protection"] = "Cloudflare", "Cloudflare Bot Management"
    elif "akamai" in header_str or "edgesuite" in header_str:
        tech["Hosting/WAF"], tech["Bot Protection"] = "Akamai CDN", "Akamai Bot Manager"
    
    if "phpsessid" in header_str or ".php" in html_low: tech["Language/Framework"] = "PHP"
    elif "jsessionid" in header_str: tech["Language/Framework"] = "Java"
    elif "x-powered-by" in headers: tech["Language/Framework"] = headers["X-Powered-By"]
    
    return tech

def analyze_file_info(file_bytes):
    """Deep Inspection for Office and Binary formats."""
    if not file_bytes: return None
    header_hex = file_bytes[:4].hex().upper()
    if header_hex == "504B0304":
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                filenames = [f.filename for f in z.infolist()]
                if any("xl/workbook.xml" in f for f in filenames):
                    return {"Type": "Microsoft Excel (OpenXML)", "MIME": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "Ext": "xlsx"}
        except: pass
        return {"Type": "ZIP Archive", "MIME": "application/zip", "Ext": "zip"}
    try:
        m = puremagic.from_string(file_bytes)[0]
        return {"Type": m.name, "MIME": m.mime, "Ext": m.extension.replace('.', '')}
    except: return {"Type": "Unknown Binary", "MIME": "application/octet-stream", "Ext": "bin"}

# --- Sidebar Navigation ---
st.sidebar.title("🛠️ Tool Suite")
app_mode = st.sidebar.radio("Navigate to:", [
    "🌐 Web Scraper Analyzer", 
    "📄 Deep File Inspector", 
    "JSON JSON Validator & Formatter"
])

# --- MODULE 1: WEB SCRAPER ANALYZER ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Tech Profiler")
    source_url = st.text_input("Enter Source URL:", value="")
    
    if st.button("Run Tech Analysis"):
        with st.spinner("Fingerprinting Website..."):
            try:
                res = chatter_requests.get(source_url, impersonate="chrome120", timeout=20)
                tech_data = detect_tech_stack(res.headers, res.text)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Status Code", res.status_code)
                c2.metric("Hosting", tech_data['Hosting/WAF'])
                c3.metric("Bot Detection", "Active" if tech_data['Bot Protection'] != "None Detected" else "None")

                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("💻 Technology Stack")
                    st.write(f"**Framework/Language:** `{tech_data['Language/Framework']}`")
                    st.write(f"**Server:** `{res.headers.get('Server', 'Hidden')}`")
                with col_right:
                    st.subheader("🛡️ Security Strategy")
                    st.info(f"**Protection Found:** {tech_data['Bot Protection']}")
                    if "None" in tech_data['Bot Protection']:
                        st.success("Strategy: Use standard BeautifulSoup/Requests.")
                    else:
                        st.warning("Strategy: Use Playwright or curl_cffi with TLS Spoofing.")
            except Exception as e: st.error(f"Failed: {e}")

# --- MODULE 2: DEEP FILE INSPECTOR ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    uploaded_file = st.file_uploader("Upload file for Magic Number analysis", type=None)
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if st.button("Identify File Type"):
            info = analyze_file_info(file_bytes)
            st.success(f"File: {uploaded_file.name}")
            st.write(f"**MIME:** `{info['MIME']}` | **True Ext:** `{info['Ext']}`")
            st.info(info['Type'])

# --- MODULE 3: JSON VALIDATOR & FORMATTER ---
elif app_mode == "JSON JSON Validator & Formatter":
    st.title("JSON JSON Validator & Formatter")
    st.write("Paste your raw JSON below to validate, format, or minify it.")

    json_input = st.text_area("Input JSON:", height=300, placeholder='{"key": "value"}')
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        format_btn = st.button("✨ Format")
    with col2:
        minify_btn = st.button("📉 Minify")

    if json_input:
        try:
            # Parse the JSON
            parsed_json = json.loads(json_input)
            
            if format_btn:
                formatted_json = json.dumps(parsed_json, indent=4, sort_keys=True)
                st.subheader("Formatted JSON")
                st.code(formatted_json, language="json")
                st.success("✅ JSON is Valid")
            
            elif minify_btn:
                minified_json = json.dumps(parsed_json, separators=(',', ':'))
                st.subheader("Minified JSON")
                st.code(minified_json, language="json")
                st.success("✅ JSON is Valid")
            
            else:
                # Default validation check
                st.success("✅ JSON is Valid")
                
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e.msg} (at line {e.lineno}, column {e.colno})")
            
            # Show a snippet of where the error might be
            lines = json_input.split('\n')
            if e.lineno <= len(lines):
                st.info(f"Problematic line: `{lines[e.lineno-1].strip()}`")

# Footer
st.sidebar.divider()
st.sidebar.caption("All-in-One Developer Scraper Suite")
