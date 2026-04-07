import streamlit as st
from curl_cffi import requests as chatter_requests
from bs4 import BeautifulSoup
import pandas as pd
import puremagic  # Handles the file type identification
import io

# Page Configuration
st.set_page_config(page_title="Pro Scraper & File Analyzer", page_icon="🛡️", layout="wide")

def get_file_type_info(url):
    """
    Downloads the start of a file to identify its true type via magic numbers.
    """
    try:
        # We only need the first 2048 bytes to identify a file type
        headers = {"Range": "bytes=0-2048", "User-Agent": "Mozilla/5.0..."}
        response = chatter_requests.get(url, impersonate="chrome120", headers=headers, timeout=10)
        
        if response.status_code in [200, 206]:
            # Identify the file type from the byte stream
            ext_info = puremagic.from_string(response.content)
            return ext_info
        return "Could not reach file"
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_url(url):
    # ... [Keep your existing analyze_url logic here] ...
    # (Ensure it returns soup and results)
    try:
        response = chatter_requests.get(url, impersonate="chrome120", timeout=30)
        is_blocked = "Access Denied" in response.text or response.status_code in [403, 401]
        soup = BeautifulSoup(response.text, 'html.parser')
        results = {
            'status_code': response.status_code,
            'is_blocked': is_blocked,
            'raw_content': response.text,
            'links': soup.find_all('a')
        }
        return results, soup, None
    except Exception as e:
        return None, None, str(e)

# --- UI ---
st.title("🛡️ Scraper Analyzer + Deep File Inspector")

url_input = st.text_input("Enter URL to Analyze:", value="https://www.tcs.com/investor-relations/financial-statements")

if st.button("Run Full Analysis"):
    data, soup, error = analyze_url(url_input)
    
    if error:
        st.error(error)
    else:
        # Display existing metrics...
        st.success(f"Status: {data['status_code']} | Site Accessed Successfully")

        st.divider()
        
        # --- NEW: FILE TYPE CHECKER SECTION ---
        st.header("📄 Source File Discovery & Validation")
        
        # Filter for links that look like files
        file_extensions = ('.pdf', '.xlsx', '.csv', '.zip', '.doc', '.docx')
        file_links = []
        for a in data['links']:
            href = a.get('href', '')
            if any(href.lower().endswith(ext) for ext in file_extensions):
                # Ensure absolute URL
                full_url = href if href.startswith('http') else f"https://www.tcs.com{href}"
                file_links.append(full_url)
        
        if file_links:
            # Remove duplicates
            file_links = list(set(file_links))
            st.write(f"Found **{len(file_links)}** potential files. Select one to verify its true type:")
            
            selected_file = st.selectbox("Pick a file to inspect:", file_links)
            
            if st.button("Validate Selected File"):
                with st.spinner("Inspecting file signature..."):
                    magic_result = get_file_type_info(selected_file)
                    
                    # Display results in a nice card
                    st.info(f"**Target:** {selected_file}")
                    
                    # puremagic returns a list of possibilities
                    if isinstance(magic_result, str):
                        st.error(magic_result)
                    else:
                        st.subheader("File Identity Analysis")
                        # Displaying as a Table
                        df_magic = pd.DataFrame([{
                            "True Extension": m.extension,
                            "MIME Type": m.mime,
                            "File Description": m.name,
                            "Confidence": "High (Byte-Match)"
                        } for m in magic_result])
                        st.table(df_magic)
                        
                        # Compare against expected
                        expected = "." + selected_file.split('.')[-1].lower()
                        actual = magic_result[0].extension.lower()
                        
                        if expected == actual:
                            st.success(f"Verification Passed: File is a genuine {actual} file.")
                        else:
                            st.warning(f"Verification Mismatch: Link says {expected}, but signature is {actual}!")
        else:
            st.info("No file links (.pdf, .xlsx, etc.) found on this page.")
