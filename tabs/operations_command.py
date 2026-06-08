import streamlit as st
import pandas as pd
from backend import get_supabase

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
            "Status": display_status,
            "Mileage": last_mileage,
            "Alerts": ", ".join(alerts) if alerts else "None"
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
            st.markdown(f'''
            <div class="van-card {v["Status"]}">
                <h4>{v["Van ID"]}</h4>
                <p style="margin: 0; font-size: 0.9em; color: #aaa;">{v["Make/Model"]}</p>
                <p style="margin: 5px 0 0 0;"><strong>{v["Status"]}</strong></p>
                <p style="margin: 0; font-size: 0.85em;">Mileage: {v["Mileage"]}</p>
                <p style="margin: 0; font-size: 0.85em; color: #fbbf24;">{v["Alerts"]}</p>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Media Inspection Drawer")
    selected_inspect = st.selectbox("Select Van to Inspect History", options=[v['Van ID'] for v in fleet_view_data])
    
    if selected_inspect:
        try:
            audit_res = supabase.table("van_audits").select("*").eq("van_id", selected_inspect).order("audit_date", desc=True).limit(5).execute()
            audits = audit_res.data
        except Exception as e:
            st.error(f"Failed to load audits: {e}")
            audits = []
            
        if audits:
            st.write(f"Showing recent audits for **{selected_inspect}**:")
            for a in audits:
                with st.expander(f"Audit on {a.get('audit_date', '')[:10]} - Mileage: {a.get('mileage', 0)}"):
                    st.write(f"**Treads (mm):** FL: {a.get('tread_fl')} | FR: {a.get('tread_fr')} | RL: {a.get('tread_rl')} | RR: {a.get('tread_rr')}")
                    st.write(f"**Fluids:** Wiper: {a.get('fluid_wiper')} | Coolant: {a.get('fluid_coolant')} | Oil: {a.get('fluid_oil')}")
                    if a.get('damage_notes'):
                        st.write(f"**Damage Notes:** {a.get('damage_notes')}")
                    if a.get('is_grounding_risk'):
                        st.error("Flagged as Grounding Risk")
                        
                    photos = a.get('photo_urls', [])
                    if photos:
                        st.markdown("**Photos:**")
                        p_cols = st.columns(len(photos))
                        for i, p in enumerate(photos):
                            with p_cols[i]:
                                st.image(p, use_column_width=True)
                    else:
                        st.info("No photos uploaded for this audit.")
        else:
            st.info("No historical audits found for this van.")
