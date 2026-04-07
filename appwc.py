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
from urllib.parse import urlparse

# --- Page Setup ---
st.set_page_config(page_title="Pro Scraper & Dev Suite", page_icon="🛡️", layout="wide")

# --- Logic Functions ---

def tidy_validate_url(url):
    """Parses a URL and returns HTML5 validation errors."""
    try:
        res = chatter_requests.get(url, impersonate="chrome120", timeout=20)
        # We use a strict parser to catch every non-compliant tag
        parser = html5lib.HTMLParser(strict=True)
        try:
            parser.parse(res.text)
            return [], res.text, None # No errors
        except html5lib.html5parser.ParseError as e:
            # html5lib stops at the first fatal error in strict mode
            return [str(e)], res.text, None
        except Exception as e:
            # Fallback for non-strict reporting (Linter style)
            linter = html5lib.HTMLParser(strict=False)
            doc = linter.parse(res.text)
            return ["Malformed structure detected (Non-fatal)"], res.text, None
    except Exception as e:
        return None, None, str(e)

def analyze_file_info(file_bytes):
    """Deep Inspection logic from previous steps."""
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
    "JSON JSON Validator & Formatter",
    "🧹 Tidy HTML Validator"
])

# --- MODULE 1: WEB SCRAPER ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Tech Profiler")
    url = st.text_input("Enter Source URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    if st.button("Run Analysis"):
        with st.spinner("Fingerprinting..."):
            try:
                res = chatter_requests.get(url, impersonate="chrome120")
                st.metric("Status", res.status_code)
                st.json(dict(res.headers))
            except Exception as e: st.error(e)

# --- MODULE 2: FILE INSPECTOR ---
elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    uploaded_file = st.file_uploader("Upload file")
    if uploaded_file:
        if st.button("Identify File Type"):
            info = analyze_file_info(uploaded_file.getvalue())
            st.info(info['Type'])

# --- MODULE 3: JSON SUITE ---
elif app_mode == "JSON JSON Validator & Formatter":
    st.title("JSON JSON Validator & Formatter")
    json_in = st.text_area("Input JSON:", height=300)
    if st.button("Validate & Format"):
        try:
            parsed = json.loads(json_in)
            st.code(json.dumps(parsed, indent=4), language="json")
            st.success("Valid JSON")
        except Exception as e: st.error(e)

# --- MODULE 4: TIDY HTML VALIDATOR (NEW) ---
elif app_mode == "🧹 Tidy HTML Validator":
    st.title("🧹 Tidy HTML Validator")
    st.write("Check if a website's HTML is compliant or 'broken'.")
    
    val_url = st.text_input("URL to Validate:", value="https://example.com")
    
    if st.button("Check HTML Health"):
        with st.spinner("Parsing HTML structure..."):
            errors, raw_html, connection_error = tidy_validate_url(val_url)
            
            if connection_error:
                st.error(f"Connection Failed: {connection_error}")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Validation Result")
                    if not errors:
                        st.success("✅ Clean HTML: No structural errors found.")
                    else:
                        st.warning(f"⚠️ Issues Found: {len(errors)}")
                        for err in errors:
                            st.write(f"- {err}")
                
                with col2:
                    st.subheader("Scraping Impact")
                    if not errors:
                        st.info("Strategy: Safe to use standard Parsers (lxml/BeautifulSoup).")
                    else:
                        st.error("Strategy: Malformed HTML detected. Use 'html5lib' in your scraper to avoid data loss.")

                with st.expander("View Cleaned Source (Tidy)"):
                    st.code(raw_html[:5000], language="html")

# Footer
st.sidebar.divider()
st.sidebar.caption("v3.0 | HTML5 / JSON / Scraper Suite")
