import streamlit as st
import time
from backend import get_supabase, compress_image, upload_photo

def sync_tread(pos, source):
    val = st.session_state[f"audit_{source}_{pos}"]
    if source == 'slider':
        st.session_state[f"audit_num_{pos}"] = val
    else:
        st.session_state[f"audit_slider_{pos}"] = val

def render_daily_audit():
    st.header("Audit")
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
    
    if "audit_photos" not in st.session_state:
        st.session_state.audit_photos = []
        
    # Initialize tread states
    for pos in ['fl', 'fr', 'rl', 'rr']:
        if f"audit_slider_{pos}" not in st.session_state:
            st.session_state[f"audit_slider_{pos}"] = 8.0
        if f"audit_num_{pos}" not in st.session_state:
            st.session_state[f"audit_num_{pos}"] = 8.0

    selected_van = st.selectbox("Select Van ID", options=list(van_options.keys()), key="audit_van_id")
    last_known_mileage = van_options.get(selected_van, 0)
    
    st.info(f"Last known mileage: **{last_known_mileage}**")
    
    current_mileage = st.number_input("Current Odometer", min_value=0, value=last_known_mileage, step=1, key="audit_mileage")
    
    st.markdown("### Tire Tread Matrix (mm)")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Front Driver Side Tire**")
        sc1, nc1 = st.columns([3, 1])
        sc1.slider("FL Slider", 0.0, 12.0, key="audit_slider_fl", on_change=sync_tread, args=("fl", "slider"), label_visibility="collapsed")
        nc1.number_input("FL Num", 0.0, 12.0, key="audit_num_fl", on_change=sync_tread, args=("fl", "num"), label_visibility="collapsed")
        
        st.markdown("**Rear Driver Side Tire**")
        sc2, nc2 = st.columns([3, 1])
        sc2.slider("RL Slider", 0.0, 12.0, key="audit_slider_rl", on_change=sync_tread, args=("rl", "slider"), label_visibility="collapsed")
        nc2.number_input("RL Num", 0.0, 12.0, key="audit_num_rl", on_change=sync_tread, args=("rl", "num"), label_visibility="collapsed")
        
    with col2:
        st.markdown("**Front Passenger Side Tire**")
        sc3, nc3 = st.columns([3, 1])
        sc3.slider("FR Slider", 0.0, 12.0, key="audit_slider_fr", on_change=sync_tread, args=("fr", "slider"), label_visibility="collapsed")
        nc3.number_input("FR Num", 0.0, 12.0, key="audit_num_fr", on_change=sync_tread, args=("fr", "num"), label_visibility="collapsed")
        
        st.markdown("**Rear Passenger Side Tire**")
        sc4, nc4 = st.columns([3, 1])
        sc4.slider("RR Slider", 0.0, 12.0, key="audit_slider_rr", on_change=sync_tread, args=("rr", "slider"), label_visibility="collapsed")
        nc4.number_input("RR Num", 0.0, 12.0, key="audit_num_rr", on_change=sync_tread, args=("rr", "num"), label_visibility="collapsed")
        
    tread_fl = st.session_state.audit_num_fl
    tread_fr = st.session_state.audit_num_fr
    tread_rl = st.session_state.audit_num_rl
    tread_rr = st.session_state.audit_num_rr
        
    st.markdown("### Fluids Panel")
    col3, col4, col5 = st.columns(3)
    with col3:
        fluid_wiper = st.radio("Wiper Fluid", ["Good", "Low"], horizontal=True, key="audit_wiper")
    with col4:
        fluid_coolant = st.radio("Coolant", ["Good", "Low"], horizontal=True, key="audit_coolant")
    with col5:
        fluid_oil = st.radio("Oil Level", ["Good", "Low"], horizontal=True, key="audit_oil")
        
    damage_notes = st.text_area("Damage Notes", placeholder="Enter any new physical damage...", key="audit_damage")
    
    st.markdown("### 📷 Live Camera Capture")
    st.caption(f"Photos captured: {len(st.session_state.audit_photos)} / 8")
    
    photo_labels = [
        "Front", "Rear",
        "Driver Side", "Passenger Side",
        "Rear Driver Side Tire", "Rear Passenger Side Tire",
        "Front Passenger Side Tire", "Front Driver Side Tire"
    ]
    
    current_idx = len(st.session_state.audit_photos)
    if current_idx < 8:
        current_label = photo_labels[current_idx]
        st.markdown(f"**Next Required Photo: {current_label}**")
        pic = st.camera_input(f"Snap {current_label}", key=f"camera_{current_idx}")
        if pic:
            st.session_state.audit_photos.append(pic)
            st.rerun()

    if st.session_state.audit_photos:
        st.markdown("**Captured Photos**")
        p_cols = st.columns(4)
        for i, p in enumerate(st.session_state.audit_photos):
            p_cols[i % 4].image(p, caption=photo_labels[i], use_column_width=True)
            
        if st.button("❌ Clear Photos", use_container_width=True):
            st.session_state.audit_photos = []
            st.rerun()
    
    st.markdown("---")
    submitted = st.button("Submit Audit", use_container_width=True, type="primary")
    
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
            if st.session_state.audit_photos:
                for idx, file in enumerate(st.session_state.audit_photos):
                    try:
                        compressed_bytes = compress_image(file)
                        url = upload_photo(selected_van, idx, compressed_bytes)
                        if url:
                            photo_urls.append(url)
                    except Exception as e:
                        st.error(f"Failed to process photo: {e}")
            
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
                    
                supabase.table("vehicles").update(update_data).eq("van_id", selected_van).execute()
                
                st.success(f"Audit for {selected_van} submitted successfully!")
                
                # Clear all form state
                keys_to_clear = [
                    "audit_van_id", "audit_mileage", 
                    "audit_slider_fl", "audit_num_fl",
                    "audit_slider_fr", "audit_num_fr",
                    "audit_slider_rl", "audit_num_rl",
                    "audit_slider_rr", "audit_num_rr",
                    "audit_wiper", "audit_coolant",
                    "audit_oil", "audit_damage", "audit_photos"
                ]
                for k in keys_to_clear:
                    if k in st.session_state:
                        del st.session_state[k]
                        
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Database execution failed: {e}")
