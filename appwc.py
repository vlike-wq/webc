import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic
import socket
import io
import zipfile
import json
import html5lib
import datetime
from urllib.parse import urlparse

# --- Page Setup ---
st.set_page_config(page_title="Ultimate Scraper Dev Suite", page_icon="🛡️", layout="wide")

# --- Global Logic Functions ---

def analyze_html_health(url):
    try:
        res = chatter_requests.get(url, impersonate="chrome120", timeout=20)
        html_content = res.text
        lines = html_content.splitlines()
        parser = html5lib.HTMLParser()
        parser.parse(html_content)
        detailed_errors = []
        for (line, col), error_type, details in parser.errors:
            msg = error_type.replace("-", " ").capitalize()
            source_snippet = "N/A"
            if line is not None and line <= len(lines):
                source_snippet = lines[line - 1].strip()
            detailed_errors.append({
                "line": line if line else 1,
                "col": col if col else 1,
                "msg": msg,
                "content": source_snippet
            })
        return detailed_errors, html_content, len(lines), None
    except Exception as e:
        return None, None, 0, str(e)

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
        return {"Type": "ASCII text... (Zip archive data, v2.0+)", "MIME": "application/zip", "Ext": "zip"}
    try:
        m = puremagic.from_string(file_bytes)[0]
        return {"Type": m.name, "MIME": m.mime, "Ext": m.extension.replace('.', '')}
    except: return {"Type": "Unknown Binary", "MIME": "application/octet-stream", "Ext": "bin"}

def detect_tech_stack(headers, html):
    tech = {"Hosting/WAF": "Unknown", "Language/Framework": "Not Disclosed", "Bot Protection": "None Detected"}
    h_str = str(headers).lower()
    html_low = html.lower()
    if "cloudflare" in h_str: tech["Hosting/WAF"], tech["Bot Protection"] = "Cloudflare", "Cloudflare Active"
    elif "akamai" in h_str: tech["Hosting/WAF"], tech["Bot Protection"] = "Akamai CDN", "Akamai Bot Manager"
    if ".php" in html_low or "phpsessid" in h_str: tech["Language/Framework"] = "PHP"
    elif "jsessionid" in h_str: tech["Language/Framework"] = "Java"
    elif "x-powered-by" in headers: tech["Language/Framework"] = headers["X-Powered-By"]
    return tech

# --- Sidebar Navigation ---
st.sidebar.title("🛠️ Dev & Scraper Suite")
app_mode = st.sidebar.radio("Navigate to:", [
    "🌐 Web Scraper Analyzer", 
    "📄 Deep File Inspector", 
    "JSON Validator & Formatter",
    "🧹 Tidy HTML Validator & Linter",
    "⏺️ Scraper Recorder"
])

# --- MODULE 1: WEB SCRAPER ANALYZER ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Tech Profiler")
    url = st.text_input("Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    if st.button("Run Profiler"):
        with st.spinner("Fingerprinting..."):
            try:
                res = chatter_requests.get(url, impersonate="chrome120")
                tech = detect_tech_stack(res.headers, res.text)
                st.metric("Status", res.status_code)
                st.write(f"**Hosting:** {tech['Hosting/WAF']} | **Language:** {tech['Language/Framework']}")
                st.json(dict(res.headers))
            except Exception as e: st.error(e)

# --- MODULE 2: DEEP FILE INSPECTOR ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    up = st.file_uploader("Upload file")
    if up:
        if st.button("Deep Scan"):
            info = analyze_file_info(up.getvalue())
            st.success(f"File: {up.name}")
            st.write(f"**MIME:** `{info['MIME']}`")
            st.info(info['Type'])

# --- MODULE 3: JSON VALIDATOR & FORMATTER ---
elif app_mode == "JSON Validator & Formatter":
    st.title("JSON Validator & Formatter")
    js_in = st.text_area("Input JSON:", height=250)
    if st.button("Process"):
        try:
            p = json.loads(js_in)
            st.code(json.dumps(p, indent=4), language="json")
            st.success("JSON Valid")
        except Exception as e: st.error(f"Invalid JSON: {e}")

# --- MODULE 4: TIDY HTML VALIDATOR & LINTER ---
elif app_mode == "🧹 Tidy HTML Validator & Linter":
    st.title("🧹 Tidy HTML Validator & Linter")
    val_url = st.text_input("URL to Lint:", value="https://example.com")
    if st.button("Start Deep Linting"):
        with st.spinner("Mapping DOM structural issues..."):
            errors, raw_html, total_lines, conn_err = analyze_html_health(val_url)
            if conn_err: st.error(f"Network Error: {conn_err}")
            else:
                score = max(0, 100 - len(errors))
                c1, c2, c3 = st.columns(3)
                c1.metric("Health Score", f"{score}%")
                c2.metric("Total Lines", total_lines)
                c3.metric("Total Issues", len(errors))
                st.divider()
                if not errors: st.success("✅ Clean HTML detected.")
                else:
                    df = pd.DataFrame(errors)
                    st.dataframe(df[['line', 'col', 'msg']], use_container_width=True)
                    for i, err in enumerate(errors[:10]):
                        with st.expander(f"Line {err['line']}: {err['msg']}"):
                            st.error(f"Error at Line {err['line']}, Col {err['col']}")
                            st.code(err['content'], language="html")

# --- MODULE 5: SCRAPER RECORDER ---
elif app_mode == "⏺️ Scraper Recorder":
    st.title("⏺️ Step-by-Step Scraper Recorder")
    st.write("Plan your scraping flow and generate Playwright automation code.")
    if 'steps' not in st.session_state: st.session_state.steps = []
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Add Recording Step")
        action = st.selectbox("Action", ["Navigate", "Wait for Selector", "Click", "Type Text", "Extract Data"])
        target = st.text_input("Target (URL or CSS Selector):")
        value = st.text_input("Value (Only for Type Text):") if action == "Type Text" else ""
        if st.button("Add Step"):
            st.session_state.steps.append({"action": action, "target": target, "value": value})
    
    with col2:
        st.subheader("Sequence")
        for i, s in enumerate(st.session_state.steps):
            st.text(f"{i+1}. {s['action']} -> {s['target']}")
        if st.button("Clear Steps"):
            st.session_state.steps = []; st.rerun()

    if st.session_state.steps:
        st.divider()
        code = "from playwright.sync_api import sync_playwright\n\ndef run():\n    with sync_playwright() as p:\n        browser = p.chromium.launch(headless=False)\n        page = browser.new_page()\n"
        for s in st.session_state.steps:
            if s['action'] == "Navigate": code += f"        page.goto('{s['target']}')\n"
            elif s['action'] == "Wait for Selector": code += f"        page.wait_for_selector('{s['target']}')\n"
            elif s['action'] == "Click": code += f"        page.click('{s['target']}')\n"
            elif s['action'] == "Type Text": code += f"        page.fill('{s['target']}', '{s['value']}')\n"
            elif s['action'] == "Extract Data": code += f"        print(page.inner_text('{s['target']}'))\n"
        code += "        browser.close()\nrun()"
        st.code(code, language="python")

# Footer
st.sidebar.divider()
st.sidebar.caption(f"v5.0 | {datetime.date.today().year} | Developer Tool Suite")
