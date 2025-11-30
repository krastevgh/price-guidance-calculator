"""
Commercial Pricing Guidance & Realization - Main Application
Entry point with Page Config, Session State, and main layout.
"""

import streamlit as st
import pandas as pd
from datetime import date
from typing import Dict, Any

from data import (
    load_reference_data,
    get_material_codes,
    get_tx_variants,
    get_classifications,
    create_empty_deal_row,
    parse_uploaded_csv,
    get_costs_expected_columns,
    get_guidance_expected_columns
)
from logic import (
    calculate_deal_realization,
    aggregate_deal_metrics,
    validate_deal_inputs,
    calculate_tx_count_from_atv
)
from components import (
    render_header,
    render_kpi_cards,
    render_deal_matrix,
    render_gap_analysis_chart,
    render_detailed_results_table,
    render_sidebar_settings,
    render_admin_settings,
    render_validation_errors,
    render_realization_breakdown
)


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Commercial Pricing Guidance",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def initialize_session_state() -> None:
    """Initialize session state variables safely."""
    if 'deal_data' not in st.session_state:
        st.session_state.deal_data = pd.DataFrame([
            create_empty_deal_row(),
            {
                'material_code': 'ProcessingService',
                'tx_variant': 'visa',
                'volume_eur': 500000.0,
                'tx_count': 5000,
                'proposed_variable_pct': 0.0,
                'proposed_fixed_eur': 0.06,
            },
        ])
    
    if 'catalog_df' not in st.session_state:
        catalog_df, costs_df, guidance_df = load_reference_data()
        st.session_state.catalog_df = catalog_df
        st.session_state.costs_df = costs_df
        st.session_state.guidance_df = guidance_df
    
    if 'custom_costs_df' not in st.session_state:
        st.session_state.custom_costs_df = None
    
    if 'custom_guidance_df' not in st.session_state:
        st.session_state.custom_guidance_df = None


def get_active_data() -> Dict[str, pd.DataFrame]:
    """Get the active reference data (custom if uploaded, default otherwise)."""
    costs_df = (
        st.session_state.custom_costs_df
        if st.session_state.custom_costs_df is not None
        else st.session_state.costs_df
    )
    
    guidance_df = (
        st.session_state.custom_guidance_df
        if st.session_state.custom_guidance_df is not None
        else st.session_state.guidance_df
    )
    
    return {
        'catalog_df': st.session_state.catalog_df,
        'costs_df': costs_df,
        'guidance_df': guidance_df
    }


def handle_file_uploads(admin_settings: Dict[str, Any]) -> None:
    """Process uploaded CSV files."""
    if admin_settings['costs_file'] is not None:
        try:
            costs_df = parse_uploaded_csv(
                admin_settings['costs_file'],
                get_costs_expected_columns()
            )
            st.session_state.custom_costs_df = costs_df
        except ValueError as e:
            st.sidebar.error(f"Costs CSV Error: {str(e)}")
    
    if admin_settings['guidance_file'] is not None:
        try:
            guidance_df = parse_uploaded_csv(
                admin_settings['guidance_file'],
                get_guidance_expected_columns()
            )
            guidance_df['valid_from'] = pd.to_datetime(guidance_df['valid_from'])
            guidance_df['valid_to'] = pd.to_datetime(guidance_df['valid_to'])
            st.session_state.custom_guidance_df = guidance_df
        except ValueError as e:
            st.sidebar.error(f"Guidance CSV Error: {str(e)}")


def update_tx_counts(deal_data: pd.DataFrame, atv: float) -> pd.DataFrame:
    """Update transaction counts based on ATV when volume changes."""
    updated_data = deal_data.copy()
    
    for idx, row in updated_data.iterrows():
        expected_tx = calculate_tx_count_from_atv(row['volume_eur'], atv)
        if pd.isna(row['tx_count']) or row['tx_count'] == 0:
            updated_data.at[idx, 'tx_count'] = expected_tx
    
    return updated_data


def main() -> None:
    """Main application entry point."""
    configure_page()
    initialize_session_state()
    
    sidebar_settings = render_sidebar_settings(
        classifications=get_classifications(),
        default_date=date.today()
    )
    
    admin_settings = render_admin_settings()
    handle_file_uploads(admin_settings)
    
    render_header(sidebar_settings['merchant_name'])
    
    active_data = get_active_data()
    
    if st.session_state.custom_costs_df is not None or st.session_state.custom_guidance_df is not None:
        st.info("Using custom uploaded data files")
    
    edited_deal_data = render_deal_matrix(
        deal_data=st.session_state.deal_data,
        material_codes=get_material_codes(),
        tx_variants=get_tx_variants(),
        atv=sidebar_settings['atv']
    )
    
    if not edited_deal_data.equals(st.session_state.deal_data):
        st.session_state.deal_data = edited_deal_data
    
    if not edited_deal_data.empty and len(edited_deal_data) > 0:
        is_valid, errors = validate_deal_inputs(edited_deal_data)
        
        if not is_valid:
            render_validation_errors(errors)
        else:
            results_df = calculate_deal_realization(
                deal_inputs_df=edited_deal_data,
                guidance_df=active_data['guidance_df'],
                costs_df=active_data['costs_df'],
                deal_date=sidebar_settings['deal_date'],
                classification=sidebar_settings['classification']
            )
            
            metrics = aggregate_deal_metrics(results_df)
            
            render_kpi_cards(metrics)
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                render_gap_analysis_chart(results_df)
            
            with col2:
                render_realization_breakdown(results_df)
            
            render_detailed_results_table(results_df)
    else:
        st.info("Add products to the deal matrix above to begin pricing analysis.")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Commercial Pricing Guidance v1.0")
    st.sidebar.caption(f"Deal Date: {sidebar_settings['deal_date']}")


if __name__ == "__main__":
    main()
