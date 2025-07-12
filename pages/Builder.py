# streamlit_app_title: EA Builder
# ---
# title: EA Deliverables Builder
# icon: 📁
# ---
import streamlit as st
import os
import json
import pandas as pd
from io import StringIO, BytesIO
from datetime import datetime
from openai import OpenAI
import matplotlib.pyplot as plt
import seaborn as sns
import re  # 👈 ADD THIS
import os
from openai import OpenAI
# --- Setup OpenAI Client ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Directory ---
CATALOGUE_DIR = "catalogues"
os.makedirs(CATALOGUE_DIR, exist_ok=True)

st.set_page_config(page_title="EA Deliverables Builder", layout="wide")
st.title("📂 EA Deliverables Builder – DevoteamAI²")
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
        <img src="https://www.devoteam.com/wp-content/themes/lsac-devoteam/assets/images/logo-devoteam.svg" width="180"/>
    </div>
    """,
    unsafe_allow_html=True
)
# --- Load and classify all interview files ---
app_data = []
biz_data = []

for f in os.listdir(CATALOGUE_DIR):
    if f.endswith(".json"):
        with open(os.path.join(CATALOGUE_DIR, f), "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                role = data.get("stakeholder_role", "").lower()
                if "application" in role:
                    app_data.append(data)
                elif "business" in role:
                    biz_data.append(data)
            except Exception as e:
                st.warning(f"⚠️ Could not load {f}: {e}")

# --- Select Deliverable ---
st.subheader("🛠️ Choose what you want to generate:")
options = [
    "📘 Build Business Catalogue",
    "📘 Build Application Catalogue",
    "🔗 Build Integration Matrix",
    "⚠️ Build Gap Analysis",
    "🔥 ARM Heatmap – Application Perspective",
    "📊 ARM Heatmap – Business Perspective"
]
action = st.radio("Deliverable Type:", options)

# --- Extract markdown table from GPT ---
def extract_markdown_table(output_text):
    table_lines = []
    inside = False
    for line in output_text.splitlines():
        if line.strip().startswith("|") and line.count("|") >= 2:
            inside = True
            table_lines.append(line.strip())
        elif inside and not line.strip():
            break
    if not table_lines:
        return None
    try:
        df = pd.read_csv(StringIO("\n".join(table_lines)), sep="|", engine="python", skipinitialspace=True)
        df = df.dropna(axis=1, how="all")
        df.columns = [col.strip() for col in df.columns]
        df = df[1:] if df.columns.equals(df.iloc[0]) else df
        return df
    except Exception as e:
        st.warning(f"⚠️ Table parsing failed: {e}")
        return None

# --- Advanced App Heatmap

def build_app_heatmap():
    rows = []
    for app in app_data:
        rows.append({
            "Application": app.get("application_name", "Unnamed"),
            "Line of Business": app.get("line_of_business", "N/A").strip().lower(),
            "Category": app.get("category_type", "Unspecified").strip().lower()
        })

    df = pd.DataFrame(rows)

    if df.empty:
        st.warning("⚠️ No application data found.")
        return

    # Pivot for count matrix
    count_matrix = df.groupby(["Line of Business", "Category"]).size().unstack(fill_value=0)

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(count_matrix, annot=True, fmt="d", cmap="YlGnBu", linewidths=0.5, cbar=True, ax=ax)
    ax.set_title("🗺️ Application Heatmap by LOB vs Category", fontsize=14)
    ax.set_xlabel("Application Category")
    ax.set_ylabel("Line of Business")
    st.pyplot(fig)

    # Optionally display detailed list
    with st.expander("📋 View Applications per Cell"):
        st.dataframe(df)

# --- Advanced Business Heatmap


def build_business_heatmap():
    st.markdown("### 🧊 Business Capability Heatmap")

    if not biz_data:
        st.warning("⚠️ No Business Owner data found.")
        return

    rows = []

    for f in os.listdir(CATALOGUE_DIR):
        if not f.startswith("BusinessOwner_") or not f.endswith(".json"):
            continue

        filepath = os.path.join(CATALOGUE_DIR, f)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                interview = json.load(file)

            # Extract line of business from filename
            match = re.search(r'BusinessOwner_(.*?)__', f)
            lob = match.group(1).replace('_', ' ').strip().title() if match else "Unknown"

            raw_caps = interview.get("capabilities", "")

            # Parse raw string of capabilities
            if isinstance(raw_caps, str):
                parsed_caps = [cap.strip("- ").strip() for cap in raw_caps.split("\n") if cap.strip()]
            else:
                parsed_caps = []

            def clean_cap(cap):
                return re.sub(r'cab\s*\d+\s*[:\-]?\s*', '', cap, flags=re.IGNORECASE).strip().capitalize()

            cleaned_caps = [clean_cap(cap) for cap in parsed_caps]

            for cap in cleaned_caps:
                rows.append({
                    "Line of Business": lob,
                    "Capability": cap
                })

        except Exception as e:
            st.warning(f"⚠️ Error reading {f}: {e}")

    if not rows:
        st.warning("⚠️ No capabilities could be extracted from Business Owner files.")
        return

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # Heatmap of capability count per LOB
    count_matrix = df.groupby(["Line of Business", "Capability"]).size().unstack(fill_value=0)

    st.markdown("### 🔥 Heatmap View (Count of Capabilities by Line of Business)")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(count_matrix, cmap="YlGnBu", annot=True, fmt="d", linewidths=0.5, cbar=True, ax=ax)
    ax.set_xlabel("Capability")
    ax.set_ylabel("Line of Business")
    ax.set_title("Business Capability Coverage Heatmap")
    st.pyplot(fig)

# --- Generate Deliverable ---
if st.button("🤖 Generate Using DevoteamAI²"):
    with st.spinner("🧠 Thinking like an architect..."):

        if action == "📘 Build Application Catalogue":
            input_data = app_data
            prompt = """
You are an expert Application Architect. Build a TOGAF-aligned Application Catalogue from the following interviews. Output ONLY a clean markdown table with: App Name, Business Line, Category, Status, Tech Stack, Stakeholder.
"""
        elif action == "📘 Build Business Catalogue":
            input_data = biz_data
            prompt = """
You are an expert Business Architect. Build a TOGAF-aligned Business Capability Catalogue. Output ONLY a clean markdown table with: Capability Name, Description, Related Department, Pain Point, TOGAF Layer.
"""
        elif action == "🔗 Build Integration Matrix":
            rows = []
            for app in app_data:
                app_name = app.get("application_name", "Unknown")
                integrations = app.get("integrations", [])
                for entry in integrations:
                    rows.append({
                        "Source App": entry.get("Source App", app_name),
                        "Target App": entry.get("Target App", ""),
                        "Interface Type": entry.get("Interface Type", ""),
                        "Protocol": entry.get("Protocol", ""),
                        "Frequency": entry.get("Frequency", "")
                    })

            if not rows:
                st.warning("⚠️ No integration data found.")
            else:
                df = pd.DataFrame(rows)
                st.success("✅ Integration Matrix built from structured JSON.")
                st.dataframe(df)

                excel_io = BytesIO()
                with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Integration Matrix")
                excel_io.seek(0)
                st.download_button(
                    label="📥 Download as Excel",
                    data=excel_io.getvalue(),
                    file_name="Integration_Matrix.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            input_data = []
            prompt = ""

        elif action == "⚠️ Build Gap Analysis":
            input_data = app_data
            prompt = """
You're a TOGAF compliance consultant. Analyze the following interviews and generate a structured Gap Analysis. Use markdown bullets or tables showing Gap, Impact, and Recommendation.
"""
        elif action == "🔥 ARM Heatmap – Application Perspective":
            build_app_heatmap()
            input_data = []
            prompt = ""
        elif action == "📊 ARM Heatmap – Business Perspective":
            build_business_heatmap()
            input_data = []
            prompt = ""
        else:
            input_data = []
            prompt = "No action selected."

        if prompt.strip():
            final_prompt = f"{prompt.strip()}\n\nData:\n{json.dumps(input_data, indent=2)}"

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a senior Enterprise Architect."},
                        {"role": "user", "content": final_prompt}
                    ]
                )
                output = response.choices[0].message.content
                st.success("✅ Deliverable Generated!")
                st.markdown(output)

                if "Catalogue" in action or "Matrix" in action:
                    df = extract_markdown_table(output)
                    if df is not None:
                        st.dataframe(df)
                        excel_io = BytesIO()
                        with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name="Deliverable")
                        excel_io.seek(0)
                        st.download_button(
                            label="📥 Download as Excel",
                            data=excel_io.getvalue(),
                            file_name="EA_Deliverable.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.warning("⚠️ Could not extract table for Excel download.")
            except Exception as e:
                st.error(f"❌ GPT Error: {e}")

# --- Footer ---
st.markdown("""
---
<center>Powered by <strong>DevoteamAI²</strong> | Use Case 2</center>
""")
