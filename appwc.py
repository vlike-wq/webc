import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import socket
import io
import zipfile
import re
from urllib.parse import urlparse

# --- Page Setup ---
st.set_page_config(page_title="Pro Scraper & Tech Profiler", page_icon="🛡️", layout="wide")

def detect_tech_stack(headers, html):
    """Identifies hosting, language, and bot detection signatures."""
    tech = {
        "Hosting/WAF": "Unknown",
        "Language/Framework": "Not Disclosed",
        "Bot Protection": "None Detected"
    }
    
    header_str = str(headers).lower()
    html_low = html.lower()

    # 1. Detect Hosting / WAF
    if "cloudflare" in header_str or "cf-ray" in header_str:
        tech["Hosting/WAF"] = "Cloudflare"
        tech["Bot Protection"] = "Cloudflare Under Attack / Bot Management"
    elif "akamai" in header_str or "edgesuite" in header_str:
        tech["Hosting/WAF"] = "Akamai CDN"
        tech["Bot Protection"] = "Akamai Bot Manager"
    elif "cloudfront" in header_str:
        tech["Hosting/WAF"] = "Amazon CloudFront"
    elif "litespeed" in header_str:
        tech["Hosting/WAF"] = "LiteSpeed Server"
    elif "nginx" in header_str:
        tech["Hosting/WAF"] = "Nginx"

    # 2. Detect Language / Framework
    if "phpsessid" in header_str or ".php" in html_low:
        tech["Language/Framework"] = "PHP"
    elif "jsessionid" in header_str or "java" in header_str:
        tech["Language/Framework"] = "Java (JSP/Spring)"
    elif "asp.net" in header_str or "__viewstate" in html_low:
        tech["Language/Framework"] = "ASP.NET"
    elif "x-powered-by" in headers:
        tech["Language/Framework"] = headers["X-Powered-By"]
    elif "next.js" in html_low or "__next" in html_low:
        tech["Language/Framework"] = "Next.js (React)"

    # 3. Specific Bot Detection Scripts
    if "datadome" in html_low or "dd_captcha" in html_low:
        tech["Bot Protection"] = "DataDome (High Difficulty)"
    elif "imperva" in header_str or "incapsula" in header_str:
        tech["Bot Protection"] = "Imperva / Incapsula"
    elif "recaptcha" in html_low:
        tech["Bot Protection"] = "Google reCAPTCHA"

    return tech

def get_server_ip(url):
    try:
        hostname = urlparse(url).hostname
        return socket.gethostbyname(hostname) if hostname else "N/A"
    except: return "Unknown"

def analyze_file_info(file_bytes):
    if not file_bytes: return None
    header_hex = file_bytes[:4].hex().upper()
    if header_hex == "504B0304":
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                filenames = [f.filename for f in z.infolist()]
                if any("xl/workbook.xml" in f for f in filenames):
                    return {"Type": "Microsoft Excel (OpenXML)", "MIME": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "Ext": "xlsx"}
                elif any("word/document.xml" in f for f in filenames):
                    return {"Type": "Microsoft Word (OpenXML)", "MIME": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Ext": "docx"}
        except: pass
    if header_hex == "504B0304":
        return {"Type": "ZIP Archive", "MIME": "application/zip", "Ext": "zip"}
    if header_hex == "25504446":
        return {"Type": "PDF Document", "MIME": "application/pdf", "Ext": "pdf"}
    try:
        m = puremagic.from_string(file_bytes)[0]
        return {"Type": m.name, "MIME": m.mime, "Ext": m.extension.replace('.', '')}
    except: return {"Type": "Unknown Binary", "MIME": "application/octet-stream", "Ext": "bin"}

# --- Navigation ---
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a Module:", ["🌐 Web Scraper Analyzer", "📄 Deep File Inspector"])

if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Tech Stack Profiler")
    source_url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    
    if st.button("Run Tech Analysis"):
        with st.spinner("Fingerprinting Website..."):
            try:
                res = chatter_requests.get(source_url, impersonate="chrome120", timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                tech_data = detect_tech_stack(res.headers, res.text)
                
                # Visual Dashboard
                c1, c2, c3 = st.columns(3)
                c1.metric("Status", res.status_code)
                c2.metric("Server IP", get_server_ip(source_url))
                c3.metric("Links", len(soup.find_all('a')))

                st.divider()
                
                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("💻 Technology Stack")
                    st.write(f"**Hosting / Infrastructure:** `{tech_data['Hosting/WAF']}`")
                    st.write(f"**Programming Language:** `{tech_data['Language/Framework']}`")
                    st.write(f"**Server Type:** `{res.headers.get('Server', 'Hidden')}`")
                
                with col_right:
                    st.subheader("🛡️ Security & Bot Detection")
                    if tech_data['Bot Protection'] == "None Detected":
                        st.success(f"**Bot Detection:** {tech_data['Bot Protection']}")
                    else:
                        st.warning(f"**Bot Detection:** {tech_data['Bot Protection']}")
                    
                    # Logic for Scraping Strategy
                    st.write("**Scraping Difficulty:**")
                    if "Cloudflare" in tech_data['Hosting/WAF'] or "Akamai" in tech_data['Hosting/WAF']:
                        st.error("Hard (Requires TLS Fingerprinting / Proxies)")
                    else:
                        st.success("Easy (Standard Requests should work)")

                with st.expander("View HTTP Response Headers"):
                    st.json(dict(res.headers))
            except Exception as e:
                st.error(f"Analysis Failed: {e}")

elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    tab1, tab2 = st.tabs(["Analyze via URL", "Upload Local File"])
    
    with tab1:
        file_url = st.text_input("Direct File URL:")
        if st.button("Inspect Remote"):
            if file_url:
                with st.spinner("Fetching bytes..."):
                    try:
                        resp = chatter_requests.get(file_url, impersonate="chrome120", headers={"Range": "bytes=0-8192"}, timeout=15)
                        info = analyze_file_info(resp.content)
                        st.subheader("File Properties")
                        st.write(f"**Origin (IP):** {get_server_ip(file_url)}")
                        st.write(f"**MIME Type:** `{info['MIME']}`")
                        st.info(info['Type'])
                    except Exception as e: st.error(f"Failed: {e}")

    with tab2:
        uploaded_file = st.file_uploader("Upload file", type=None)
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            if st.button("Run Deep Scan"):
                info = analyze_file_info(file_bytes)
                st.success(f"Analysis Complete: {uploaded_file.name}")
                st.write(f"**MIME Type:** `{info['MIME']}` | **Size:** {len(file_bytes)/1024:.2f} KB")
                st.info(info['Type'])
