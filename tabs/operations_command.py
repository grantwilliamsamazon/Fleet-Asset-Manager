import streamlit as st
import pandas as pd
from backend import get_supabase

@st.dialog("Van Profile Manager", width="large")
def manage_van_dialog(selected_van, vehicles):
    supabase = get_supabase()
    van_record = next((v for v in vehicles if v['van_id'] == selected_van), None)
    
    if not van_record:
        st.error("Van record not found.")
        return
        
    tab1, tab2 = st.tabs(["Vehicle Info", "Audit Logs"])
    
    with tab1:
        st.subheader("Edit Vehicle Details")
        with st.form(f"edit_van_{selected_van}"):
            new_vin = st.text_input("VIN", value=van_record.get('vin', ''))
            new_make = st.text_input("Make/Model", value=van_record.get('make_model', ''))
            
            status_opts = ["Active", "Maintenance", "Grounded"]
            current_status = van_record.get('status', 'Active')
            if current_status not in status_opts:
                status_opts.append(current_status)
                
            new_status = st.selectbox("Status", options=status_opts, index=status_opts.index(current_status))
            new_mileage = st.number_input("Last Mileage", value=van_record.get('last_mileage', 0), step=1)
            
            if st.form_submit_button("Save Vehicle Info", type="primary"):
                try:
                    supabase.table("vehicles").update({
                        "vin": new_vin,
                        "make_model": new_make,
                        "status": new_status,
                        "last_mileage": new_mileage
                    }).eq("van_id", selected_van).execute()
                    st.success("Vehicle info updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update vehicle: {e}")
                    
    with tab2:
        try:
            audit_res = supabase.table("van_audits").select("*").eq("van_id", selected_van).order("audit_date", desc=True).limit(10).execute()
            audits = audit_res.data
        except Exception as e:
            st.error(f"Failed to load audits: {e}")
            audits = []
            
        if audits:
            photo_labels = [
                "Front", "Rear",
                "Driver Side", "Passenger Side",
                "Rear Driver Side Tire", "Rear Passenger Side Tire",
                "Front Passenger Side Tire", "Front Driver Side Tire"
            ]
            
            st.write(f"Showing recent audits for **{selected_van}**:")
            for a in audits:
                audit_id = a.get('id')
                date_str = a.get('audit_date', '')[:10]
                with st.expander(f"Audit on {date_str} - Mileage: {a.get('mileage', 0)}"):
                    st.write(f"**Treads (mm):** FL: {a.get('tread_fl')} | FR: {a.get('tread_fr')} | RL: {a.get('tread_rl')} | RR: {a.get('tread_rr')}")
                    st.write(f"**Fluids:** Wiper: {a.get('fluid_wiper')} | Coolant: {a.get('fluid_coolant')} | Oil: {a.get('fluid_oil')}")
                    if a.get('damage_notes'):
                        st.write(f"**Damage Notes:** {a.get('damage_notes')}")
                    if a.get('is_grounding_risk'):
                        st.error("Flagged as Grounding Risk")
                        
                    photos = a.get('photo_urls', [])
                    if photos:
                        st.markdown("**Photos:**")
                        # 4 photos per row
                        for i in range(0, len(photos), 4):
                            row_photos = photos[i:i+4]
                            p_cols = st.columns(4)
                            for j, p in enumerate(row_photos):
                                idx = i + j
                                label = photo_labels[idx] if idx < len(photo_labels) else f"Photo {idx+1}"
                                with p_cols[j]:
                                    st.image(p, caption=label, use_column_width=True)
                    else:
                        st.info("No photos uploaded for this audit.")
                        
                    st.markdown("---")
                    
                    # Edit / Delete actions
                    del_col, edit_col = st.columns([1, 3])
                    with del_col:
                        if st.button("🗑️ Delete Audit", key=f"del_{audit_id}", type="secondary"):
                            try:
                                supabase.table("van_audits").delete().eq("id", audit_id).execute()
                                st.success("Audit deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Delete failed: {e}")
                                
                    with st.expander("✏️ Edit Audit Text"):
                        with st.form(f"edit_audit_{audit_id}"):
                            e_mil = st.number_input("Mileage", value=a.get('mileage',0), step=1)
                            
                            c1, c2 = st.columns(2)
                            e_fl = c1.slider("Tread FL", 0.0, 12.0, float(a.get('tread_fl', 8.0)), key=f"efl_{audit_id}")
                            e_fr = c2.slider("Tread FR", 0.0, 12.0, float(a.get('tread_fr', 8.0)), key=f"efr_{audit_id}")
                            e_rl = c1.slider("Tread RL", 0.0, 12.0, float(a.get('tread_rl', 8.0)), key=f"erl_{audit_id}")
                            e_rr = c2.slider("Tread RR", 0.0, 12.0, float(a.get('tread_rr', 8.0)), key=f"err_{audit_id}")
                            
                            c3, c4, c5 = st.columns(3)
                            wiper_val = a.get('fluid_wiper', 'Good')
                            cool_val = a.get('fluid_coolant', 'Good')
                            oil_val = a.get('fluid_oil', 'Good')
                            
                            e_wip = c3.radio("Wiper", ["Good", "Low"], index=0 if wiper_val=="Good" else 1, key=f"ew_{audit_id}")
                            e_cool = c4.radio("Coolant", ["Good", "Low"], index=0 if cool_val=="Good" else 1, key=f"ec_{audit_id}")
                            e_oil = c5.radio("Oil", ["Good", "Low"], index=0 if oil_val=="Good" else 1, key=f"eo_{audit_id}")
                            
                            e_notes = st.text_area("Damage Notes", value=a.get('damage_notes', ''), key=f"en_{audit_id}")
                            
                            if st.form_submit_button("Update Audit"):
                                try:
                                    supabase.table("van_audits").update({
                                        "mileage": e_mil,
                                        "tread_fl": e_fl, "tread_fr": e_fr,
                                        "tread_rl": e_rl, "tread_rr": e_rr,
                                        "fluid_wiper": e_wip, "fluid_coolant": e_cool, "fluid_oil": e_oil,
                                        "damage_notes": e_notes
                                    }).eq("id", audit_id).execute()
                                    st.success("Audit updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Update failed: {e}")
        else:
            st.info("No historical audits found for this van.")

def render_operations_command():
    st.header("Operations Command")
    
    supabase = get_supabase()
    
    try:
        vehicles_res = supabase.table("vehicles").select("*").order("van_id").execute()
        vehicles = vehicles_res.data
    except Exception as e:
        st.error(f"Failed to fetch fleet data: {e}")
        return
        
    if not vehicles:
        st.info("No vehicles found.")
        return

    # Process KPIs & Alerts
    active_count = 0
    maintenance_count = 0
    grounded_count = 0
    
    fleet_view_data = []
    
    for v in vehicles:
        van_id = v['van_id']
        status = v['status']
        last_mileage = v.get('last_mileage', 0) or 0
        last_oil = v.get('last_oil_change_mileage', 0) or 0
        last_tire = v.get('last_tire_rotation_mileage', 0) or 0
        
        alerts = []
        # Smart maintenance alerts
        if (last_mileage - last_oil) >= 5000:
            alerts.append("Oil Change Due")
        if (last_mileage - last_tire) >= 10000:
            alerts.append("Tire Rotation Due")
            
        display_status = status
        # If alerts exist and not already Grounded, mark as Maintenance visually
        if alerts and status == 'Active':
            display_status = 'Maintenance'
            
        if display_status == 'Active': active_count += 1
        elif display_status == 'Maintenance': maintenance_count += 1
        else: grounded_count += 1
        
        fleet_view_data.append({
            "Van ID": van_id,
            "Make/Model": v.get('make_model', ''),
            "VIN": v.get('vin', 'N/A'),
            "Status": display_status,
            "Mileage": last_mileage,
            "Alerts": ", ".join(alerts) if alerts else ""
        })

    # KPI Status Summary
    st.markdown("### Fleet KPI Summary")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div style="color:#888;">Active</div><div class="metric-value status-active">{active_count}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div style="color:#888;">Maintenance Needed</div><div class="metric-value status-maintenance">{maintenance_count}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div style="color:#888;">Grounded</div><div class="metric-value status-grounded">{grounded_count}</div></div>', unsafe_allow_html=True)

    # Fleet Matrix Layout
    st.markdown("### Fleet Matrix")
    
    cols = st.columns(4)
    for idx, v in enumerate(fleet_view_data):
        col = cols[idx % 4]
        with col:
            alerts_html = f'<p style="margin: 0; font-size: 0.85em; color: #fbbf24;">{v["Alerts"]}</p>' if v["Alerts"] else ''
            st.markdown(f'''
            <div class="van-card {v["Status"]}">
                <h4>{v["Van ID"]}</h4>
                <p style="margin: 0; font-size: 0.9em; color: #aaa;">{v["Make/Model"]}</p>
                <p style="margin: 0; font-size: 0.85em; color: #888;">VIN: {v["VIN"]}</p>
                <p style="margin: 5px 0 0 0;"><strong>{v["Status"]}</strong></p>
                <p style="margin: 0; font-size: 0.85em;">Mileage: {v["Mileage"]}</p>
                {alerts_html}
            </div>
            ''', unsafe_allow_html=True)
            if st.button("Manage Van Data & Logs", key=f"btn_{v['Van ID']}", use_container_width=True):
                manage_van_dialog(v["Van ID"], vehicles)
