import streamlit as st
import time
from backend import get_supabase, compress_image, upload_photo

def render_daily_audit():
    st.header("Daily Pad Audit")
    st.markdown("Perform mobile-optimized daily checks on physical assets.")
    
    supabase = get_supabase()
    
    # Fetch vehicles
    try:
        response = supabase.table("vehicles").select("van_id, last_mileage").order("van_id").execute()
        vehicles = response.data
    except Exception as e:
        st.error(f"Error fetching vehicles: {e}")
        vehicles = []
        
    if not vehicles:
        st.warning("No vehicles found in database.")
        return
        
    van_options = {v['van_id']: v['last_mileage'] for v in vehicles}
    
    with st.form("audit_form", clear_on_submit=True):
        selected_van = st.selectbox("Select Van ID", options=list(van_options.keys()))
        last_known_mileage = van_options.get(selected_van, 0)
        
        st.info(f"Last known mileage: **{last_known_mileage}**")
        
        current_mileage = st.number_input("Current Odometer", min_value=0, value=last_known_mileage, step=1)
        
        st.markdown("### Tire Tread Matrix (mm)")
        col1, col2 = st.columns(2)
        with col1:
            tread_fl = st.slider("Front Left", 0.0, 12.0, 8.0, 0.1)
            tread_rl = st.slider("Rear Left", 0.0, 12.0, 8.0, 0.1)
        with col2:
            tread_fr = st.slider("Front Right", 0.0, 12.0, 8.0, 0.1)
            tread_rr = st.slider("Rear Right", 0.0, 12.0, 8.0, 0.1)
            
        st.markdown("### Fluids Panel")
        col3, col4, col5 = st.columns(3)
        with col3:
            fluid_wiper = st.radio("Wiper Fluid", ["Good", "Low"], horizontal=True)
        with col4:
            fluid_coolant = st.radio("Coolant", ["Good", "Low"], horizontal=True)
        with col5:
            fluid_oil = st.radio("Oil Level", ["Good", "Low"], horizontal=True)
            
        damage_notes = st.text_area("Damage Notes", placeholder="Enter any new physical damage...")
        
        st.markdown("### Multi-Media Uploader")
        uploaded_files = st.file_uploader("Snap up to 8 core photos", accept_multiple_files=True, type=["jpg", "jpeg", "png", "heic"])
        
        submitted = st.form_submit_button("Submit Audit", use_container_width=True, type="primary")
        
        if submitted:
            if current_mileage < last_known_mileage:
                st.error(f"Error: Current mileage ({current_mileage}) cannot be lower than the last known mileage ({last_known_mileage}).")
                return
                
            # Grounding risk logic
            is_grounding_risk = False
            if "Low" in [fluid_wiper, fluid_coolant, fluid_oil]:
                is_grounding_risk = True
            if any(t <= 3.0 for t in [tread_fl, tread_fr, tread_rl, tread_rr]):
                is_grounding_risk = True
                
            with st.spinner("Processing asset data and photos..."):
                photo_urls = []
                if uploaded_files:
                    for idx, file in enumerate(uploaded_files[:8]):
                        try:
                            # Compress
                            compressed_bytes = compress_image(file)
                            # Upload
                            url = upload_photo(selected_van, idx, compressed_bytes)
                            if url:
                                photo_urls.append(url)
                        except Exception as e:
                            st.error(f"Failed to process photo {file.name}: {e}")
                
                # Insert Audit Record
                audit_data = {
                    "van_id": selected_van,
                    "mileage": current_mileage,
                    "tread_fl": tread_fl,
                    "tread_fr": tread_fr,
                    "tread_rl": tread_rl,
                    "tread_rr": tread_rr,
                    "fluid_wiper": fluid_wiper,
                    "fluid_coolant": fluid_coolant,
                    "fluid_oil": fluid_oil,
                    "damage_notes": damage_notes,
                    "photo_urls": photo_urls,
                    "is_grounding_risk": is_grounding_risk
                }
                
                try:
                    supabase.table("van_audits").insert(audit_data).execute()
                    
                    # Update Vehicle Matrix
                    update_data = {
                        "last_mileage": current_mileage
                    }
                    if is_grounding_risk:
                        update_data["status"] = "Grounded"
                        
                    supabase.table("vehicles").update(update_data).eq("van_id", selected_van).execute()
                    
                    st.success(f"Audit for {selected_van} submitted successfully!")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Database execution failed: {e}")
