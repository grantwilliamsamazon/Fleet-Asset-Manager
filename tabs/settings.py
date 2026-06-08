import streamlit as st
from backend import get_supabase
import json

def render_settings():
    st.header("⚙️ Settings")
    st.markdown("Configure maintenance intervals for the fleet.")
    
    supabase = get_supabase()
    
    # Fetch current settings
    try:
        res = supabase.table("settings").select("value").eq("key", "maintenance_intervals").execute()
        if res.data:
            current_intervals = res.data[0]["value"]
        else:
            current_intervals = {"Ford": {"oil": 5000, "tire": 10000}, "Ram": {"oil": 5000, "tire": 10000}}
    except Exception as e:
        st.error(f"Error fetching settings: {e}")
        current_intervals = {"Ford": {"oil": 5000, "tire": 10000}, "Ram": {"oil": 5000, "tire": 10000}}

    st.subheader("Maintenance Intervals")
    
    with st.form("settings_form"):
        st.markdown("### Ford Intervals")
        col1, col2 = st.columns(2)
        with col1:
            ford_oil = st.number_input("Ford Oil Change Interval (miles)", value=current_intervals.get("Ford", {}).get("oil", 5000), step=500)
        with col2:
            ford_tire = st.number_input("Ford Tire Rotation Interval (miles)", value=current_intervals.get("Ford", {}).get("tire", 10000), step=500)
            
        st.markdown("### Ram Intervals")
        col3, col4 = st.columns(2)
        with col3:
            ram_oil = st.number_input("Ram Oil Change Interval (miles)", value=current_intervals.get("Ram", {}).get("oil", 5000), step=500)
        with col4:
            ram_tire = st.number_input("Ram Tire Rotation Interval (miles)", value=current_intervals.get("Ram", {}).get("tire", 10000), step=500)
            
        submitted = st.form_submit_button("Save Settings", type="primary")
        if submitted:
            new_intervals = {
                "Ford": {"oil": ford_oil, "tire": ford_tire},
                "Ram": {"oil": ram_oil, "tire": ram_tire}
            }
            try:
                # Upsert settings
                supabase.table("settings").upsert({
                    "key": "maintenance_intervals",
                    "value": new_intervals
                }).execute()
                st.success("Settings saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save settings: {e}")
