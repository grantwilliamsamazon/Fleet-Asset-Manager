import streamlit as st
import time
from backend import get_supabase

def render_log_maintenance():
    st.header("Log Maintenance")
    st.markdown("Record shop services and clear maintenance alerts.")
    
    supabase = get_supabase()
    
    try:
        vehicles_res = supabase.table("vehicles").select("van_id").order("van_id").execute()
        vehicles = [v['van_id'] for v in vehicles_res.data]
    except Exception as e:
        st.error(f"Error fetching vehicles: {e}")
        vehicles = []
        
    if not vehicles:
        st.warning("No vehicles available.")
        return

    with st.form("maintenance_form", clear_on_submit=True):
        selected_van = st.selectbox("Select Van ID", options=vehicles)
        service_type = st.selectbox("Service Type", options=["Oil Change", "Tire Rotation", "Brakes", "General Repair"])
        service_mileage = st.number_input("Mileage at Service", min_value=0, step=1)
        service_notes = st.text_area("Service Notes (Optional)")
        
        submitted = st.form_submit_button("Log Service", use_container_width=True, type="primary")
        
        if submitted:
            if service_mileage == 0:
                st.error("Please enter a valid mileage.")
                return
                
            with st.spinner("Recording maintenance..."):
                # Insert event
                event_data = {
                    "van_id": selected_van,
                    "event_type": service_type,
                    "mileage_at_service": service_mileage,
                    "service_notes": service_notes
                }
                
                try:
                    supabase.table("maintenance_events").insert(event_data).execute()
                    
                    # Update target vehicle
                    update_data = {
                        "status": "Active" # Reset to Active
                    }
                    if service_type == "Oil Change":
                        update_data["last_oil_change_mileage"] = service_mileage
                    elif service_type == "Tire Rotation":
                        update_data["last_tire_rotation_mileage"] = service_mileage
                        
                    # Also ensure last_mileage isn't less than service mileage
                    v_res = supabase.table("vehicles").select("last_mileage").eq("van_id", selected_van).execute()
                    if v_res.data and v_res.data[0]['last_mileage'] < service_mileage:
                        update_data["last_mileage"] = service_mileage
                        
                    supabase.table("vehicles").update(update_data).eq("van_id", selected_van).execute()
                    
                    st.success(f"Successfully logged {service_type} for {selected_van}!")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {e}")
