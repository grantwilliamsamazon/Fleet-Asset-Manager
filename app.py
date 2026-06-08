import streamlit as st
from backend import get_supabase
from tabs.daily_audit import render_daily_audit
from tabs.operations_command import render_operations_command
from tabs.log_maintenance import render_log_maintenance

# Configure Streamlit page
st.set_page_config(
    page_title="Fleet Asset Manager",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Authentication block
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>Login Required</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            pwd = st.text_input("Enter Passcode", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if pwd == "111020":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect passcode")
    st.stop() # Stops execution of the rest of the app until authenticated

# Render Custom CSS for aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .metric-card {
        background: #1e212b;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 10px 0;
    }
    .status-active { color: #4ade80; }
    .status-maintenance { color: #fbbf24; }
    .status-grounded { color: #f87171; }
    
    .van-card {
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background: #1a1c23;
        transition: all 0.3s ease;
    }
    .van-card.Active { border-left: 4px solid #4ade80; }
    .van-card.Maintenance { border-left: 4px solid #fbbf24; }
    .van-card.Grounded { border-left: 4px solid #f87171; }
</style>
""", unsafe_allow_html=True)

st.title("🚚 DSP Fleet Asset Manager")
st.markdown("### Welcome Shrimp 🦐")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📝 Audit", "📊 Operations Command", "🛠️ Log Maintenance"])

with tab1:
    render_daily_audit()

with tab2:
    render_operations_command()

with tab3:
    render_log_maintenance()
