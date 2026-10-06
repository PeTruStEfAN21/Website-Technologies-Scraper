import json
from collections import Counter
import pandas as pd
import streamlit as st
from fetcher import Fetcher
from detector import Detector

st.set_page_config(page_title="Web Tech Profiler", page_icon="🔍", layout="wide")

st.title(" Website Technology Profiler — Dashboard")
st.markdown("Analiza stivei tehnologice pe dataset-ul de domenii + **Live Domain Scanner**.")

@st.cache_data
def load_results():
    try:
        with open("results.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

results = load_results()

if not results:
    st.warning("Nu am gasit `results.json`! Ruleaza mai intai `python main.py` pentru a genera datele.")
else:
    total_domains = len(results)
    alive_domains = sum(1 for r in results if r["status_code"] > 0)
    with_tech = sum(1 for r in results if len(r["technologies"]) > 0)

    all_techs = [tech for r in results for tech in r["technologies"]]
    tech_counts = Counter(all_techs)
    total_tools_count = len(all_techs)
    unique_tools_count = len(tech_counts)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(" Total Domenii", total_domains)
    col2.metric(" Domenii Active", f"{alive_domains} ({alive_domains * 100 // total_domains}%)")
    col3.metric(" Domenii cu Tehnologii", with_tech)
    col4.metric(" Total Tool-uri Gasite", total_tools_count, f"{unique_tools_count} unice")

    st.divider()

    left_col, right_col = st.columns([1, 1.3])

    with left_col:
        st.subheader(" Top Tehnologii Detectate")
        if tech_counts:
            df_chart = pd.DataFrame(
                tech_counts.most_common(15), 
                columns=["Technology", "Count"]
            ).set_index("Technology")
            st.bar_chart(df_chart)
        else:
            st.info("Nicio tehnologie detectata inca.")

    with right_col:
        st.subheader(" Explorator Domenii")
        
        unique_techs = ["Toate"] + sorted(list(tech_counts.keys()))
        selected_tech = st.selectbox("Filtreaza dupa tehnologie:", unique_techs)

        filtered_data = []
        for r in results:
            if selected_tech == "Toate" or selected_tech in r["technologies"]:
                err_label = r.get("error") if r.get("error") else ("OK" if r["status_code"] > 0 else "NECUNOSCUT")
                filtered_data.append({
                    "Domeniu": r["domain"],
                    "Status": r["status_code"],
                    "Status / Eroare": err_label,
                    "Tehnologii": ", ".join(r["technologies"]) if r["technologies"] else "-"
                })

        st.dataframe(pd.DataFrame(filtered_data), use_container_width=True, height=350)

st.divider()

st.subheader(" Live Domain Scanner")
st.markdown("Testeaza motorul `Fetcher` + `Detector` in timp real pe orice domeniu:")

scan_col1, scan_col2 = st.columns([3, 1])
with scan_col1:
    custom_domain = st.text_input("Introdu un domeniu (ex: avocatalinamanciu.ro, wordpress.org):", placeholder="example.com")
with scan_col2:
    st.write("")
    st.write("")
    scan_btn = st.button(" Scaneaza Acum", use_container_width=True)

if scan_btn and custom_domain:
    with st.spinner(f"Se scaneaza {custom_domain}..."):
        fetcher = Fetcher()
        detector = Detector()
        page = fetcher.fetch(custom_domain.strip())
        detected_techs = detector.detect(page)

    if page.status_code == 0:
        err_msg = page.error or "Conexiune esuata"
        st.error(f" Nu s-a putut accesa `{custom_domain}` (Eroare: **{err_msg}**).")
    else:
        st.success(f" Raspuns primit de la `{page.url}` (HTTP Status: **{page.status_code}**)")
        
        if page.error:
            st.warning(f" Nota status: **{page.error}**")

        if detected_techs:
            st.write(f"**Tehnologii identificate ({len(detected_techs)}):**", detected_techs)
        else:
            st.info("Nu s-au gasit amprente cunoscute in `signatures.json` pentru acest site.")

        with st.expander(" Vezi datele brute extrase de Fetcher (Headers, Meta, Scripts)"):
            st.json({
                "headers": page.headers,
                "meta_tag": page.meta_tag,
                "cookies": page.cookies,
                "scripts_count": len(page.scripts),
                "scripts_sample": page.scripts[:10],
                "href_sample": page.href[:10]
            })