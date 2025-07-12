import streamlit as st
import json
import os
import openai
from openai import OpenAI
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from openai import OpenAI
# -------------------------------
# GPT client setup
# -------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# Load all JSON files from /catalogues
# -------------------------------
def load_all_json(folder="catalogues"):
    contents = []
    for f in os.listdir(folder):
        if f.endswith(".json"):
            try:
                with open(os.path.join(folder, f), "r", encoding="utf-8") as file:
                    contents.append(json.load(file))
            except Exception as e:
                st.warning(f"⚠️ Failed to read {f}: {e}")
    return contents

# -------------------------------
# GPT Governance Assessment
# -------------------------------
def gpt_assess_portfolio(files: list):
    raw_json = json.dumps(files, indent=2)

    prompt = (
        "You are an experienced enterprise architecture consultant.\n\n"
        "You are analyzing a portfolio of stakeholder interviews from various systems. "
        "Each interview is represented as a JSON object containing assessment and metadata fields.\n\n"
        "Below is the full set of interviews:\n"
        f"{raw_json}\n\n"
        "Your task:\n"
        "1. Score the overall governance maturity of this portfolio across the following areas (0-100):\n"
        "- TOGAF Compliance\n"
        "- NORA Alignment\n"
        "- Business-IT Alignment\n"
        "- Digital Maturity\n"
        "- Technical Debt (lower = better)\n"
        "- Completeness\n\n"
        "2. Provide a concise analysis using bullet points (not a paragraph) that:\n"
        "- Highlights strengths with justifications\n"
        "- Lists clear weaknesses or gaps and their likely impact\n"
        "- Recommends specific improvements or actions\n"
        "- Uses clear and formal bullet points with no introduction or conclusion\n\n"
        "Return only a JSON object in this format:\n"
        "{\n"
        "  \"TOGAF Compliance\": 78,\n"
        "  \"NORA Alignment\": 65,\n"
        "  ...\n"
        "  \"Justification\": \"- Bullet 1\\n- Bullet 2\\n- Bullet 3\"\n"
        "}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# Custom Progress Bar with Colors
# -------------------------------
def render_colored_bar(label, percent):
    color = "#f8485e"  # red
    if 50 <= percent < 75:
        color = "#fcb613"  # yellow
    elif percent >= 75:
        color = "#2bb574"  # green

    st.markdown(f"""
        <div style="margin: 0.5em 0;">
            <div style="font-weight: 600; color: #3c3c3a;">{label}: {percent}%</div>
            <div style="background-color: #eee; border-radius: 5px; height: 16px; width: 100%;">
                <div style="width: {percent}%; background-color: {color}; height: 100%; border-radius: 5px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------
# Heatmap
# -------------------------------
def show_heatmap(scores):
    df = pd.DataFrame([{k: v for k, v in scores.items() if isinstance(v, (int, float))}])
    st.markdown("### 🧭 Heatmap")
    plt.figure(figsize=(10, 1.5))
    sns.heatmap(df, annot=True, cmap="coolwarm", cbar=False, fmt="g", linewidths=.5)
    st.pyplot(plt.gcf())
    plt.clf()

# -------------------------------
# Streamlit Page Entry
# -------------------------------
def governance_page():
    st.title("🛡️ Governance Validator (GPT-powered)")
    st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
        <img src="https://www.devoteam.com/wp-content/themes/lsac-devoteam/assets/images/logo-devoteam.svg" width="180"/>
    </div>
    """,
    unsafe_allow_html=True
    )
    st.markdown("Reads all files in `catalogues/`, shows progress, and gives GPT-based suggestions.")
    st.info("🧠 Running governance_page()")
    st.write("📁 Scanning folder: `catalogues`")

    files = load_all_json()
    st.success(f"✅ Loaded {len(files)} JSON file(s).")

    if not files:
        st.warning("⚠️ No valid files found.")
        return

    with st.spinner("🤖 GPT analyzing portfolio..."):
        result = gpt_assess_portfolio(files)

    if "error" in result:
        st.error(f"❌ GPT error: {result['error']}")
        return

    st.success("✅ GPT evaluation complete.")

    # Render score bars
    for k, v in result.items():
        if k == "Justification":
            continue
        if isinstance(v, (int, float)):
            render_colored_bar(k, v)

    show_heatmap(result)

    # Show GPT justification in bullet format
    if "Justification" in result:
        st.markdown("### ✏️ GPT Analysis Summary")
        for line in result["Justification"].split("\n"):
            if line.strip().startswith("-"):
                st.markdown(f"{line}")

    # Download
    st.download_button(
        label="📥 Download Governance Summary",
        data=json.dumps(result, indent=2),
        file_name="EA_governance_summary.json",
        mime="application/json"
    )

# Run the page
governance_page()
