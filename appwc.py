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
st.set_page_config(page_title="Ultimate Scraper & Dev Suite", page_icon="🛡️", layout="wide")

# --- Logic Functions ---

def analyze_html_health(url):
    """Deep Linter for HTML that maps errors to line numbers."""
    try:
        res = chatter_requests.get(url, impersonate="chrome120", timeout=20)
        html_content = res.text
        lines = html_content.splitlines()
        
        # We use html5lib's walk_tree or a filter to catch errors
        # To get specific line numbers, we capture the parser's error log
        errors = []
        parser = html5lib.HTMLParser(strict=True)
        
        try:
            parser.parse(html_content)
        except html5lib.html5parser.ParseError as e:
            # Most parsers stop at the first fatal structural error in strict mode
            errors.append({
                "line": getattr(e, 'lineno', 'Unknown'),
                "col": getattr(e, 'colno', 'Unknown'),
                "msg": str(e),
                "content": lines[e.lineno - 1].strip() if hasattr(e, 'lineno') and e.lineno <= len(lines) else "N/A"
            })
        except Exception as e:
            errors.append({"line": "?", "col": "?", "msg": f"General structural issue: {str(e)}", "content": ""})

        return errors, html_content, len(lines), None
    except Exception as e:
        return None, None, 0, str(e)

def analyze_file_info(file_bytes):
    """Deep Inspection logic for Binary/Office files."""
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
st.sidebar.title("🛠️ Tool Suite v4.0")
app_mode = st.sidebar.radio("Navigate to:", [
    "🌐 Web Scraper Analyzer", 
    "📄 Deep File Inspector", 
    "JSON Validator & Formatter",
    "🧹 Tidy HTML Validator & Linter"
])

# --- MODULE 1 & 2 & 3 (Keeping original logic for brevity) ---
if app_mode == "🌐 Web Scraper Analyzer":
    st.title("🌐 Web Scraper & Tech Profiler")
    url = st.text_input("URL:", value="https://www.tcs.com/investor-relations/financial-statements")
    if st.button("Analyze"):
        with st.spinner("Probing..."):
            res = chatter_requests.get(url, impersonate="chrome120")
            st.json(dict(res.headers))

elif app_mode == "📄 Deep File Inspector":
    st.title("📄 Deep File Inspector")
    uploaded_file = st.file_uploader("Upload file")
    if uploaded_file:
        info = analyze_file_info(uploaded_file.getvalue())
        st.info(info['Type'])

elif app_mode == "JSON Validator & Formatter":
    st.title("JSON Validator & Formatter")
    json_in = st.text_area("Input JSON:")
    if st.button("Process"):
        try:
            parsed = json.loads(json_in)
            st.code(json.dumps(parsed, indent=4), language="json")
        except Exception as e: st.error(e)

# --- MODULE 4: ENHANCED TIDY HTML LINTER ---
elif app_mode == "🧹 Tidy HTML Validator & Linter":
    st.title("🧹 Tidy HTML Validator & Linter")
    st.write("Deep scan for structural HTML issues with line-by-line reporting.")
    
    val_url = st.text_input("URL to Lint:", value="https://example.com")
    
    if st.button("Start Deep Linting"):
        with st.spinner("Scanning DOM for errors..."):
            errors, raw_html, total_lines, conn_error = analyze_html_health(val_url)
            
            if conn_error:
                st.error(f"Network Error: {conn_error}")
            else:
                # 1. Health Score Calculation
                error_count = len(errors)
                health_score = max(0, 100 - (error_count * 5)) # Each error drops score by 5%
                
                c1, c2, c3 = st.columns(3)
                c1.metric("HTML Health Score", f"{health_score}%")
                c2.metric("Total Lines Scanned", total_lines)
                c3.metric("Structural Issues", error_count)

                st.divider()

                if not errors:
                    st.success("✅ **W3C Compliant (Approx):** No fatal structural errors detected in the first pass.")
                else:
                    st.subheader("🚩 Issue Report")
                    # Convert errors to Dataframe for clean display
                    df_errs = pd.DataFrame(errors)
                    st.table(df_errs[['line', 'col', 'msg']])

                    for err in errors:
                        with st.expander(f"Detailed view: Error at Line {err['line']}"):
                            st.warning(f"**Issue:** {err['msg']}")
                            st.write("**Problematic Code:**")
                            st.code(err['content'], language="html")
                            st.info("💡 **Scraper Tip:** This error can cause parsers to miss the closing tags of parent containers, leading to 'leaky' data extraction.")

                # 2. The "Tidy" Fixer
                st.subheader("🛠 Automated Repair (Tidy Preview)")
                if st.button("Generate Repaired HTML"):
                    # BeautifulSoup with html5lib automatically "fixes" the tree
                    repaired_soup = BeautifulSoup(raw_html, 'html5lib')
                    st.code(repaired_soup.prettify()[:10000], language="html")
                    st.success("The code above has been automatically balanced (all tags closed and nested correctly).")

# Footer
st.sidebar.divider()
st.sidebar.caption("v4.0 | Advanced Bot Detection & HTML Linter")
