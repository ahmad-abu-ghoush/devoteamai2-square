# streamlit_app_title: Stakeholders Interviewer
import streamlit as st
from openai import OpenAI
import time
import os
import json
from datetime import datetime
import os
from openai import OpenAI
# --- Replace with your OpenAI API key ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Known Users Mapping ---
known_users = {
    "ahmad": "Application Owner",
    "ibrahim": "Application Owner",
    "wajdi": "Application Owner",
    "omar": "Business Owner",
    "shadi": "Business Owner",
    "khalaf": "Business Owner"
}

# --- Interview Questions per Role ---
questions_app_owner = [
    {"field": "application_name", "question": "What is the Application Name?", "options": []},
    {"field": "category_type", "question": "What is the Application Category Type?", "options": ["Core System", "Supporting System", "Integration Layer", "BI/Reporting Tool", "Mobile App", "External Portal"]},
    {"field": "line_of_business", "question": "Which Line of Business does it support?", "options": []},
    {"field": "status", "question": "What is the current Application Status?", "options": ["Active", "Under Development", "Retired", "On Hold"]},
    {"field": "technology", "question": "What is the Technology Stack (e.g., Java, .NET, Node.js, Python)?", "options": []},
     # 🔽 Integration questions added here
    {"field": "integrations", "question": "Let’s collect integration details for this application. Please use the form below to add integrations.", "type": "custom"}
]

questions_business_owner = [
    {"field": "business_domain", "question": "What is your business domain or department?", "options": []},
    {"field": "capabilities", "question": "List the key business capabilities in your domain.", "options": []},
    {"field": "pain_points", "question": "What are the main pain points in current operations?", "options": []},
    {"field": "kpis", "question": "What KPIs or performance metrics do you use to evaluate success?", "options": []},
    {"field": "critical_systems", "question": "Which systems or applications are critical to your operations?", "options": []}
]
example_phrases = [
    "give me example", "give me examples", "can you give me example", "can you give me examples",
    "what are the options", "what are examples", "examples please", "show me example", "i need example"
]

# --- GPT Validator ---
def validate_answer(question_text, user_input, options):
    prompt = f"""
You are a helpful EA assistant conducting an interview.
Question: '{question_text}'
User's answer: '{user_input}'
Examples (if needed): {', '.join(options) if options else 'N/A'}

Rules:
- If the answer is asking for help (e.g., "give me examples", "what are the options", "can you clarify"), return: ❌EXAMPLE
- If the user asks for help, give example values.
- If unclear, say "I didn't understand" and give examples.
- If valid, reply ONLY with: ✅
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GPT error: {e}"

# --- Init Session State ---
if "role_selected" not in st.session_state:
    st.session_state.role_selected = False
    st.session_state.show_welcome = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "just_advanced" not in st.session_state:
    st.session_state.just_advanced = False

# --- Streamlit Config ---
st.set_page_config(page_title="DevoteamAI² Chatbot")
st.title("🤖 Role-Based EA Catalogue Interview – DevoteamAI²")
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
        <img src="https://www.devoteam.com/wp-content/themes/lsac-devoteam/assets/images/logo-devoteam.svg" width="180"/>
    </div>
    """,
    unsafe_allow_html=True
)
if st.button("📁 EA Deliverables Builder"):
    st.switch_page("pages/Builder.py")


# Add this inside the routing logic:
if st.button("📊 Governance Validator"):
    st.switch_page("pages/Governance.py")



# --- Show welcome if needed ---
if st.session_state.get("show_welcome", False):
    st.chat_message("assistant").write(
        f"👋 Welcome back {st.session_state.user_name}! You're an **{st.session_state.role}**."
    )
    st.session_state.show_welcome = False

# --- Ask for User Name and resolve role ---
if not st.session_state.role_selected:
    st.markdown("👋 Hello! Let's start with your name:")
    user_name_input = st.chat_input("Please enter your first name")

    if user_name_input:
        name_clean = user_name_input.strip().lower()
        st.chat_message("user").write(user_name_input)

        detected_role = known_users.get(name_clean)
        st.session_state.user_name = user_name_input.title()

        if detected_role:
            st.session_state.role = detected_role
            st.session_state.role_selected = True
            st.session_state.show_welcome = True
            st.rerun()
        else:
            st.chat_message("assistant").write(f"Hi {user_name_input.title()}, we couldn't find you in our records. Please select your role:")
            chosen = st.radio("I am a:", ["Application Owner", "Business Owner"], key="manual_role")
            if st.button("Continue"):
                st.session_state.role = chosen
                st.session_state.role_selected = True
                st.session_state.show_welcome = True
                st.rerun()
    st.stop()

# --- Load question set ---
question_set = questions_app_owner if st.session_state.role == "Application Owner" else questions_business_owner

# --- Show chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Ask first question if not started yet ---
if st.session_state.question_index < len(question_set) and not st.session_state.messages:
    first_q = question_set[st.session_state.question_index]["question"]
    st.chat_message("assistant").markdown(first_q)
    st.session_state.messages.append({"role": "assistant", "content": first_q})


# --- Chat logic for remaining questions ---
if st.session_state.question_index < len(question_set):
    current_q = question_set[st.session_state.question_index]
    user_input = st.chat_input("Your answer...")

    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        user_input_clean = user_input.strip().lower()
        if any(phrase in user_input_clean for phrase in example_phrases):
            feedback = "❌EXAMPLE"
        else:
            feedback = validate_answer(current_q["question"], user_input, current_q["options"])

        if feedback.strip() == "✅":
            st.session_state.answers[current_q["field"]] = user_input
            st.session_state.question_index += 1
            st.session_state.just_advanced = True

        elif feedback.strip() == "❌EXAMPLE":
            msg = f"Examples: {', '.join(current_q['options']) if current_q['options'] else 'No predefined examples.'}"
            st.chat_message("assistant").markdown(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").markdown("Please provide your answer again or type 'skip' to move on.")
            st.session_state.messages.append({"role": "assistant", "content": "Please provide your answer again or type 'skip' to move on."})
            st.session_state.just_advanced = False

        else:
            error_msg = "⚠️ That answer wasn't clear. Please rephrase or type 'skip'."
            st.chat_message("assistant").markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.session_state.just_advanced = False



# --- Handle custom grouped integrations form ---
if (
    st.session_state.question_index < len(question_set)
    and question_set[st.session_state.question_index].get("type") == "custom"
    and question_set[st.session_state.question_index]["field"] == "integrations"
):
    st.chat_message("assistant").markdown("Please fill out integration details below. You can add multiple rows:")

    if "integrations" not in st.session_state.answers:
        st.session_state.answers["integrations"] = []

    with st.form("integration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            source_app = st.text_input("Source Application")
        with col2:
            target_app = st.text_input("Target Application")

        col3, col4 = st.columns(2)
        with col3:
            interface_type = st.selectbox("Interface Type", ["API", "Batch", "Webhook", "Message Queue", "Other"])
        with col4:
            protocol = st.selectbox("Protocol", ["HTTPS", "HTTP", "SFTP", "AMQP", "MQTT", "Other"])

        frequency = st.selectbox("Frequency", ["Real-Time", "Hourly", "Daily", "Weekly", "On Demand"])
        submitted = st.form_submit_button("Add Integration")

    if submitted:
        st.session_state.answers["integrations"].append({
            "Source App": source_app,
            "Target App": target_app,
            "Interface Type": interface_type,
            "Protocol": protocol,
            "Frequency": frequency
        })

    if st.session_state.answers["integrations"]:
        st.markdown("### 🔄 Current Integrations")
        st.dataframe(st.session_state.answers["integrations"], use_container_width=True)

    if st.button("✅ Done with Integrations"):
        st.session_state.question_index += 1
        st.session_state.just_advanced = True
        st.rerun()

    st.stop()

# --- Show next question after correct answer
if st.session_state.just_advanced and st.session_state.question_index < len(question_set):
    next_q = question_set[st.session_state.question_index]["question"]
    st.chat_message("assistant").markdown(next_q)
    st.session_state.messages.append({"role": "assistant", "content": next_q})
    st.session_state.just_advanced = False

# --- End of Interview
if st.session_state.question_index >= len(question_set):
    st.success("🎉 Interview complete! Here's a summary of your input:")
    st.chat_message("assistant").markdown("```json\n" + json.dumps(st.session_state.answers, indent=2) + "\n```")

    try:
        os.makedirs("catalogues", exist_ok=True)

        role_prefix = st.session_state.role.replace(" ", "")
        name = st.session_state.answers.get("application_name") or st.session_state.answers.get("business_domain") or "entity"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{role_prefix}_{safe_name}_{timestamp}.json"
        filepath = os.path.join("catalogues", filename)


        export_data = st.session_state.answers.copy()
        export_data["stakeholder_role"] = st.session_state.role

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
 

        st.chat_message("assistant").markdown(f"✅ Interview responses saved to: `{filepath}`")

    except Exception as e:
        st.chat_message("assistant").markdown(f"❌ Error saving file: `{str(e)}`")

    if st.button("🔄 Restart"):
        for key in ["messages", "answers", "question_index", "role", "role_selected", "just_advanced", "user_name", "show_welcome"]:
            st.session_state.pop(key, None)
        st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown('<div style="text-align: center; color: gray;">Powered by <strong>DevoteamAI²</strong> | MVP Demo</div>', unsafe_allow_html=True)
