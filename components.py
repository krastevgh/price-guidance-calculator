"""
Components Module for Commercial Pricing Guidance & Realization.
Contains UI rendering functions for KPI Cards, Data Editor, and Charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional


def render_kpi_cards(metrics: Dict[str, Any]) -> None:
    """
    Render KPI cards showing Total Deal Value, Total Margin, and Global Realization %.
    """
    with st.container(border=True):
        st.subheader("Deal Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Total Deal Value",
                value=f"€{metrics['total_deal_value']:,.0f}",
                help="Sum of all volume amounts in the deal"
            )
        
        with col2:
            margin_value = metrics['total_margin']
            margin_delta = None
            if margin_value < 0:
                margin_color = "inverse"
            else:
                margin_color = "normal"
            
            st.metric(
                label="Total Margin",
                value=f"€{margin_value:,.2f}",
                help="Actual Revenue minus Total Cost"
            )
        
        with col3:
            realization = metrics['global_realization_pct']
            
            if realization < 95:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #ffebee;
                        border: 1px solid #ef5350;
                        border-radius: 8px;
                        padding: 16px;
                        text-align: center;
                    ">
                        <p style="color: #666; margin: 0; font-size: 14px;">Global Realization %</p>
                        <p style="color: #d32f2f; margin: 8px 0 0 0; font-size: 32px; font-weight: 600;">{realization:.1f}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.metric(
                    label="Global Realization %",
                    value=f"{realization:.1f}%",
                    help="Actual Revenue / Target Revenue * 100"
                )


def render_deal_matrix(
    deal_data: pd.DataFrame,
    material_codes: List[str],
    tx_variants: List[str],
    atv: float
) -> pd.DataFrame:
    """
    Render the editable deal matrix using st.data_editor.
    Returns the edited DataFrame.
    """
    with st.container(border=True):
        st.subheader("Deal Matrix")
        st.caption("Add or edit product lines for this deal. Transaction Count auto-calculates from Volume/ATV but can be manually adjusted.")
        
        column_config = {
            "material_code": st.column_config.SelectboxColumn(
                "Material Code",
                options=material_codes,
                required=True,
                width="medium"
            ),
            "tx_variant": st.column_config.SelectboxColumn(
                "Tx Variant",
                options=tx_variants,
                required=True,
                width="small"
            ),
            "volume_eur": st.column_config.NumberColumn(
                "Volume (EUR)",
                min_value=0,
                max_value=1000000000,
                step=1000,
                format="€%.0f",
                required=True,
                width="medium"
            ),
            "tx_count": st.column_config.NumberColumn(
                "Tx Count",
                min_value=0,
                max_value=100000000,
                step=100,
                format="%d",
                required=True,
                width="small"
            ),
            "proposed_variable_pct": st.column_config.NumberColumn(
                "Proposed Variable %",
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                format="%.2f%%",
                required=True,
                width="medium",
                help="Enter as percentage (e.g., 0.60 for 0.60%)"
            ),
            "proposed_fixed_eur": st.column_config.NumberColumn(
                "Proposed Fixed EUR",
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                format="€%.4f",
                required=True,
                width="medium"
            ),
        }
        
        edited_df = st.data_editor(
            deal_data,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="deal_matrix_editor"
        )
        
        return edited_df


def render_gap_analysis_chart(results_df: pd.DataFrame) -> None:
    """
    Render Plotly bar chart comparing Target Revenue, Actual Revenue, and Total Cost.
    """
    with st.container(border=True):
        st.subheader("Gap Analysis")
        
        if results_df.empty:
            st.info("Add products to the deal matrix to see the gap analysis.")
            return
        
        valid_results = results_df[results_df['target_revenue'].notna()].copy()
        
        if valid_results.empty:
            st.warning("No guidance found for the selected products. Unable to show gap analysis.")
            return
        
        valid_results['product_label'] = (
            valid_results['material_code'].str[:8] + 
            '-' + 
            valid_results['tx_variant']
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Target Revenue',
            x=valid_results['product_label'],
            y=valid_results['target_revenue'],
            marker_color='#1976D2',
            text=valid_results['target_revenue'].apply(lambda x: f'€{x:,.0f}'),
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='Actual Revenue',
            x=valid_results['product_label'],
            y=valid_results['actual_revenue'],
            marker_color='#4CAF50',
            text=valid_results['actual_revenue'].apply(lambda x: f'€{x:,.0f}'),
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='Total Cost',
            x=valid_results['product_label'],
            y=valid_results['total_cost'],
            marker_color='#FF5722',
            text=valid_results['total_cost'].apply(lambda x: f'€{x:,.0f}'),
            textposition='outside'
        ))
        
        fig.update_layout(
            barmode='group',
            xaxis_title='Product',
            yaxis_title='Amount (EUR)',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=400,
            margin=dict(t=60, b=60),
            plot_bgcolor='rgba(0,0,0,0)',
        )
        
        fig.update_xaxes(tickangle=-45)
        fig.update_yaxes(gridcolor='lightgray', gridwidth=0.5)
        
        st.plotly_chart(fig, use_container_width=True)


def render_detailed_results_table(results_df: pd.DataFrame) -> None:
    """
    Render a detailed results table with calculated metrics.
    """
    with st.container(border=True):
        st.subheader("Detailed Results")
        
        if results_df.empty:
            st.info("Add products to the deal matrix to see detailed results.")
            return
        
        display_df = results_df.copy()
        
        display_columns = [
            'material_code',
            'tx_variant',
            'volume_eur',
            'tx_count',
            'proposed_variable_pct',
            'proposed_fixed_eur',
            'actual_revenue',
            'target_revenue',
            'total_cost',
            'actual_margin',
            'realization_pct',
            'guidance_status'
        ]
        
        available_columns = [col for col in display_columns if col in display_df.columns]
        display_df = display_df[available_columns]
        
        column_config = {
            "material_code": st.column_config.TextColumn("Material Code", width="medium"),
            "tx_variant": st.column_config.TextColumn("Variant", width="small"),
            "volume_eur": st.column_config.NumberColumn("Volume (EUR)", format="€%.0f"),
            "tx_count": st.column_config.NumberColumn("Tx Count", format="%d"),
            "proposed_variable_pct": st.column_config.NumberColumn("Prop. Var %", format="%.2f%%"),
            "proposed_fixed_eur": st.column_config.NumberColumn("Prop. Fixed", format="€%.4f"),
            "actual_revenue": st.column_config.NumberColumn("Actual Rev", format="€%.2f"),
            "target_revenue": st.column_config.NumberColumn("Target Rev", format="€%.2f"),
            "total_cost": st.column_config.NumberColumn("Total Cost", format="€%.2f"),
            "actual_margin": st.column_config.NumberColumn("Margin", format="€%.2f"),
            "realization_pct": st.column_config.NumberColumn("Realization %", format="%.1f%%"),
            "guidance_status": st.column_config.TextColumn("Status", width="small"),
        }
        
        st.dataframe(
            display_df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )


def render_sidebar_settings(
    classifications: List[str],
    default_date: Any
) -> Dict[str, Any]:
    """
    Render sidebar settings and return the selected values.
    """
    st.sidebar.header("Deal Settings")
    
    merchant_name = st.sidebar.text_input(
        "Merchant Name",
        value="New Merchant",
        help="Enter the merchant name for this deal"
    )
    
    deal_date = st.sidebar.date_input(
        "Deal Date",
        value=default_date,
        help="Select the effective date for pricing guidance"
    )
    
    classification = st.sidebar.selectbox(
        "Price Guidance Classification",
        options=classifications,
        index=0,
        help="Select the regional pricing tier"
    )
    
    atv = st.sidebar.number_input(
        "Avg Transaction Value (ATV)",
        min_value=1.0,
        max_value=100000.0,
        value=100.0,
        step=10.0,
        help="Used to auto-calculate transaction count from volume"
    )
    
    return {
        'merchant_name': merchant_name,
        'deal_date': deal_date,
        'classification': classification,
        'atv': atv
    }


def render_admin_settings() -> Dict[str, Any]:
    """
    Render admin settings expander with file upload options.
    Returns uploaded files if any.
    """
    with st.sidebar.expander("Admin Settings"):
        st.caption("Upload custom CSV files to override default data")
        
        costs_file = st.file_uploader(
            "Upload Costs CSV",
            type=['csv'],
            key="costs_uploader",
            help="CSV with columns: material_code, tx_variant, region_classification, cost_variable, cost_fixed_eur"
        )
        
        guidance_file = st.file_uploader(
            "Upload Guidance CSV",
            type=['csv'],
            key="guidance_uploader",
            help="CSV with columns: material_code, tx_variant, price_guidance_classification, min_vol_eur, max_vol_eur, valid_from, valid_to, advised_fee_variable, advised_fee_fixed_eur"
        )
        
        if costs_file is not None or guidance_file is not None:
            st.success("Custom data uploaded!")
        
        return {
            'costs_file': costs_file,
            'guidance_file': guidance_file
        }


def render_header(merchant_name: str) -> None:
    """
    Render the page header with merchant name.
    """
    st.title("Commercial Pricing Guidance & Realization")
    
    if merchant_name:
        st.markdown(f"**Merchant:** {merchant_name}")


def render_validation_errors(errors: List[str]) -> None:
    """
    Display validation errors if any.
    """
    if errors:
        with st.container(border=True):
            st.error("Validation Errors")
            for error in errors:
                st.write(f"- {error}")


def render_realization_breakdown(results_df: pd.DataFrame) -> None:
    """
    Render a breakdown of realization by product line.
    """
    with st.container(border=True):
        st.subheader("Realization by Product")
        
        if results_df.empty:
            st.info("Add products to see realization breakdown.")
            return
        
        valid_results = results_df[results_df['realization_pct'].notna()].copy()
        
        if valid_results.empty:
            st.warning("No guidance available to calculate realization.")
            return
        
        col1, col2, col3 = st.columns(3)
        
        grouped = valid_results.groupby('material_code').agg({
            'actual_revenue': 'sum',
            'target_revenue': 'sum',
            'actual_margin': 'sum'
        }).reset_index()
        
        grouped['realization'] = (grouped['actual_revenue'] / grouped['target_revenue'] * 100).round(1)
        
        for idx, row in grouped.iterrows():
            col_idx = idx % 3
            target_col = [col1, col2, col3][col_idx]
            
            with target_col:
                realization = row['realization']
                color = "#d32f2f" if realization < 95 else "#388e3c"
                
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f5f5f5;
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                        margin-bottom: 8px;
                    ">
                        <p style="color: #666; margin: 0; font-size: 12px;">{row['material_code'][:12]}</p>
                        <p style="color: {color}; margin: 4px 0; font-size: 24px; font-weight: 600;">{realization:.1f}%</p>
                        <p style="color: #666; margin: 0; font-size: 11px;">Margin: €{row['actual_margin']:,.0f}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
