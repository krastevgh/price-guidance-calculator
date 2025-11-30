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
    get_pricing_expected_columns,
    parse_uploaded_csv,
    create_default_deal_data_for_product,
    lookup_pricing,
    hydrate_new_rows
)
from logic import (
    calculate_deal_realization,
    aggregate_deal_metrics,
    aggregate_all_products,
    validate_deal_inputs,
    update_tx_counts_for_product,
    filter_valid_rows
)
from components import (
    render_header,
    render_kpi_cards,
    render_product_deal_matrix,
    render_gap_analysis_chart,
    render_detailed_results_table,
    render_sidebar_settings,
    render_admin_settings,
    render_validation_errors,
    render_realization_breakdown,
    render_export_section,
    render_historical_comparison,
    render_drill_down_analysis,
    render_scenario_comparison,
    render_save_deal_controls
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
    if 'catalog_df' not in st.session_state:
        catalog_df, pricing_df = load_reference_data()
        st.session_state.catalog_df = catalog_df
        st.session_state.pricing_df = pricing_df
    
    if 'custom_pricing_df' not in st.session_state:
        st.session_state.custom_pricing_df = None
    
    material_codes = get_material_codes()
    pricing_df = get_active_pricing_df()
    
    for material_code in material_codes:
        key = f'deal_data_{material_code}'
        if key not in st.session_state:
            st.session_state[key] = create_default_deal_data_for_product(
                material_code, pricing_df
            )
    
    if 'saved_deals' not in st.session_state:
        st.session_state.saved_deals = []
    
    if 'saved_scenarios' not in st.session_state:
        st.session_state.saved_scenarios = []


def get_active_pricing_df() -> pd.DataFrame:
    """Get the active pricing data (custom if uploaded, default otherwise)."""
    if st.session_state.custom_pricing_df is not None:
        return st.session_state.custom_pricing_df
    return st.session_state.pricing_df


def handle_file_uploads(admin_settings: Dict[str, Any]) -> None:
    """Process uploaded CSV files."""
    if admin_settings['pricing_file'] is not None:
        try:
            pricing_df = parse_uploaded_csv(
                admin_settings['pricing_file'],
                get_pricing_expected_columns()
            )
            st.session_state.custom_pricing_df = pricing_df
        except ValueError as e:
            st.sidebar.error(f"Pricing CSV Error: {str(e)}")


def update_targets_from_pricing(
    deal_data: pd.DataFrame,
    material_code: str,
    pricing_df: pd.DataFrame
) -> pd.DataFrame:
    """Update target prices in deal data based on region classification changes."""
    if deal_data.empty:
        return deal_data
    
    updated_data = deal_data.copy()
    
    for idx, row in updated_data.iterrows():
        tx_variant = row.get('tx_variant', None)
        classification = row.get('region_classification', None)
        
        if pd.isna(tx_variant) or pd.isna(classification):
            continue
        if str(tx_variant).strip() == '' or str(classification).strip() == '':
            continue
        
        pricing = lookup_pricing(pricing_df, material_code, str(tx_variant), str(classification))
        
        if pricing['found']:
            updated_data.at[idx, 'target_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            updated_data.at[idx, 'target_fixed_eur'] = round(pricing['target_fixed'], 4)
    
    return updated_data


def main() -> None:
    """Main application entry point."""
    configure_page()
    initialize_session_state()
    
    sidebar_settings = render_sidebar_settings(
        default_date=date.today()
    )
    
    admin_settings = render_admin_settings()
    handle_file_uploads(admin_settings)
    
    render_header(sidebar_settings['merchant_name'])
    
    global_atv = sidebar_settings['global_atv']
    ecom_split_pct = sidebar_settings['ecom_split_pct']
    industry = sidebar_settings['industry']
    
    st.markdown(f"**Industry:** {industry} | **ATV:** €{global_atv:.2f} | **ECOM/POS:** {ecom_split_pct}%/{100-ecom_split_pct}%")
    
    pricing_df = get_active_pricing_df()
    
    if st.session_state.custom_pricing_df is not None:
        st.info("Using custom uploaded pricing data")
    
    st.markdown("## Deal Configuration")
    st.caption("Configure pricing for each product line. Target prices are pre-populated based on region - adjust Proposed prices as your sale price.")
    
    material_codes = get_material_codes()
    product_deal_data: Dict[str, pd.DataFrame] = {}
    product_results: Dict[str, pd.DataFrame] = {}
    all_valid = True
    all_errors = []
    
    for material_code in material_codes:
        session_key = f'deal_data_{material_code}'
        current_data = st.session_state[session_key]
        
        current_data = hydrate_new_rows(current_data, material_code, pricing_df)
        current_data = update_tx_counts_for_product(current_data, global_atv)
        current_data = update_targets_from_pricing(current_data, material_code, pricing_df)
        
        edited_data = render_product_deal_matrix(
            material_code=material_code,
            deal_data=current_data,
            pricing_df=pricing_df
        )
        
        if not edited_data.equals(st.session_state[session_key]):
            edited_data = hydrate_new_rows(edited_data, material_code, pricing_df)
            edited_data = update_tx_counts_for_product(edited_data, global_atv)
            edited_data = update_targets_from_pricing(edited_data, material_code, pricing_df)
            st.session_state[session_key] = edited_data
        
        product_deal_data[material_code] = edited_data
        
        if not edited_data.empty:
            is_valid, errors = validate_deal_inputs(edited_data)
            if not is_valid:
                all_valid = False
                all_errors.extend([f"{material_code}: {e}" for e in errors])
    
    if all_errors:
        render_validation_errors(all_errors)
    
    has_data = any(not df.empty for df in product_deal_data.values())
    
    if has_data and all_valid:
        for material_code, deal_data in product_deal_data.items():
            if not deal_data.empty:
                valid_deal_data = filter_valid_rows(deal_data)
                if not valid_deal_data.empty:
                    use_ecom_split = material_code in ['AcquiringService', 'ProcessingService']
                    results_df = calculate_deal_realization(
                        deal_inputs_df=valid_deal_data,
                        pricing_df=pricing_df,
                        material_code=material_code,
                        ecom_split_pct=ecom_split_pct if use_ecom_split else 100.0
                    )
                    product_results[material_code] = results_df
                else:
                    product_results[material_code] = pd.DataFrame()
            else:
                product_results[material_code] = pd.DataFrame()
        
        global_metrics = aggregate_all_products(product_results)
        
        st.markdown("---")
        st.markdown("## Analysis Results")
        
        render_kpi_cards(global_metrics)
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            render_gap_analysis_chart(product_results)
        
        with col2:
            render_realization_breakdown(product_results)
        
        render_detailed_results_table(product_results)
        
        render_drill_down_analysis(product_results)
        
        render_export_section(
            all_results=product_results,
            metrics=global_metrics,
            merchant_name=sidebar_settings['merchant_name'],
            deal_date=sidebar_settings['deal_date']
        )
        
        saved_data = render_save_deal_controls(
            merchant_name=sidebar_settings['merchant_name'],
            deal_date=sidebar_settings['deal_date'],
            metrics=global_metrics,
            all_results=product_results
        )
        
        if saved_data:
            if saved_data['type'] == 'deal':
                st.session_state.saved_deals.append(saved_data)
                st.success(f"Deal '{saved_data['name']}' saved successfully!")
            else:
                st.session_state.saved_scenarios.append(saved_data)
                st.success(f"Scenario '{saved_data['name']}' saved successfully!")
            st.rerun()
        
        st.markdown("---")
        
        render_historical_comparison(st.session_state.saved_deals)
        
        render_scenario_comparison(st.session_state.saved_scenarios)
    else:
        st.info("Configure products in the deal matrices above to see analysis results.")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Commercial Pricing Guidance v2.0")
    st.sidebar.caption(f"Deal Date: {sidebar_settings['deal_date']}")


if __name__ == "__main__":
    main()
