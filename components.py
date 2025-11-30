"""
Components Module for Commercial Pricing Guidance & Realization.
Contains UI rendering functions for KPI Cards, Data Editor, and Charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from datetime import datetime
import io

from data import get_classifications, get_tx_variants_for_material


def render_kpi_cards(metrics: Dict[str, Any]) -> None:
    """
    Render KPI cards showing Total Deal Value, Total Margin, and Global Realization %.
    """
    with st.container(border=True):
        st.subheader("Deal Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Deal Value",
                value=f"€{metrics['total_deal_value']:,.0f}",
                help="Sum of all volume amounts in the deal"
            )
        
        with col2:
            st.metric(
                label="Total Actual Margin",
                value=f"€{metrics['total_actual_margin']:,.2f}",
                help="Actual Revenue minus Total Cost"
            )
        
        with col3:
            st.metric(
                label="Total Target Margin",
                value=f"€{metrics['total_target_margin']:,.2f}",
                help="Target Revenue minus Total Cost"
            )
        
        with col4:
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
                        <p style="color: #d32f2f; margin: 8px 0 0 0; font-size: 28px; font-weight: 600;">{realization:.1f}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.metric(
                    label="Global Realization %",
                    value=f"{realization:.1f}%",
                    help="Actual Margin / Target Margin * 100"
                )


def render_product_deal_matrix(
    material_code: str,
    deal_data: pd.DataFrame,
    pricing_df: pd.DataFrame,
    key_suffix: str = ""
) -> pd.DataFrame:
    """
    Render an editable deal matrix for a specific product line.
    Includes per-row classification, ATV, and target/proposed pricing.
    """
    tx_variants = get_tx_variants_for_material(material_code)
    classifications = get_classifications()
    
    product_labels = {
        'AcquiringService': 'Acquiring Service',
        'ProcessingService': 'Processing Service',
        'RevenueProtectService': 'Revenue Protect Service'
    }
    
    with st.expander(f"**{product_labels.get(material_code, material_code)}**", expanded=True):
        st.caption(f"Configure pricing for {product_labels.get(material_code, material_code)}. Target prices are pre-populated - adjust Proposed prices as your sale price.")
        
        column_config = {
            "tx_variant": st.column_config.SelectboxColumn(
                "Tx Variant",
                options=tx_variants,
                required=True,
                width="small"
            ),
            "region_classification": st.column_config.SelectboxColumn(
                "Region",
                options=classifications,
                required=True,
                width="medium"
            ),
            "volume_eur": st.column_config.NumberColumn(
                "Volume (EUR)",
                min_value=0,
                max_value=1000000000,
                step=10000,
                format="€%.0f",
                required=True,
                width="medium"
            ),
            "atv": st.column_config.NumberColumn(
                "ATV (EUR)",
                min_value=1.0,
                max_value=10000.0,
                step=5.0,
                format="€%.2f",
                required=True,
                width="small",
                help="Average Transaction Value"
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
            "target_variable_pct": st.column_config.NumberColumn(
                "Target Var %",
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                format="%.4f%%",
                required=True,
                width="small",
                help="Target variable fee percentage"
            ),
            "target_fixed_eur": st.column_config.NumberColumn(
                "Target Fixed",
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                format="€%.4f",
                required=True,
                width="small",
                help="Target fixed fee per transaction"
            ),
            "proposed_variable_pct": st.column_config.NumberColumn(
                "Proposed Var %",
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                format="%.4f%%",
                required=True,
                width="small",
                help="Your proposed variable fee (sale price)"
            ),
            "proposed_fixed_eur": st.column_config.NumberColumn(
                "Proposed Fixed",
                min_value=0.0,
                max_value=10.0,
                step=0.01,
                format="€%.4f",
                required=True,
                width="small",
                help="Your proposed fixed fee (sale price)"
            ),
        }
        
        edited_df = st.data_editor(
            deal_data,
            column_config=column_config,
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            key=f"deal_matrix_{material_code}_{key_suffix}"
        )
        
        return edited_df


def render_product_results(
    material_code: str,
    results_df: pd.DataFrame,
    metrics: Dict[str, Any]
) -> None:
    """
    Render results summary for a specific product line.
    """
    product_labels = {
        'AcquiringService': 'Acquiring Service',
        'ProcessingService': 'Processing Service',
        'RevenueProtectService': 'Revenue Protect Service'
    }
    
    if results_df.empty:
        return
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        
        realization = metrics['global_realization_pct']
        color = "#d32f2f" if realization < 95 else "#388e3c"
        
        with col1:
            st.markdown(f"**{product_labels.get(material_code, material_code)}**")
        
        with col2:
            st.metric("Actual Margin", f"€{metrics['total_actual_margin']:,.2f}")
        
        with col3:
            st.metric("Target Margin", f"€{metrics['total_target_margin']:,.2f}")
        
        with col4:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <span style="color: {color}; font-size: 24px; font-weight: 600;">{realization:.1f}%</span>
                    <p style="color: #666; margin: 0; font-size: 12px;">Realization</p>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_gap_analysis_chart(all_results: Dict[str, pd.DataFrame]) -> None:
    """
    Render Plotly bar chart comparing Target Margin, Actual Margin, and Cost.
    """
    with st.container(border=True):
        st.subheader("Margin Gap Analysis")
        
        combined_results = []
        for material_code, results_df in all_results.items():
            if not results_df.empty:
                combined_results.append(results_df)
        
        if not combined_results:
            st.info("Add products to the deal matrices to see the gap analysis.")
            return
        
        all_df = pd.concat(combined_results, ignore_index=True)
        
        all_df['product_label'] = (
            all_df['material_code'].str[:8] + '-' + all_df['tx_variant']
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Target Margin',
            x=all_df['product_label'],
            y=all_df['target_margin'],
            marker_color='#1976D2',
            text=all_df['target_margin'].apply(lambda x: f'€{x:,.0f}'),
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='Actual Margin',
            x=all_df['product_label'],
            y=all_df['actual_margin'],
            marker_color='#4CAF50',
            text=all_df['actual_margin'].apply(lambda x: f'€{x:,.0f}'),
            textposition='outside'
        ))
        
        fig.add_trace(go.Bar(
            name='Total Cost',
            x=all_df['product_label'],
            y=all_df['total_cost'],
            marker_color='#FF5722',
            text=all_df['total_cost'].apply(lambda x: f'€{x:,.0f}'),
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
        
        st.plotly_chart(fig, width="stretch")


def render_detailed_results_table(all_results: Dict[str, pd.DataFrame]) -> None:
    """
    Render a detailed results table with calculated metrics.
    """
    with st.container(border=True):
        st.subheader("Detailed Results")
        
        combined_results = []
        for material_code, results_df in all_results.items():
            if not results_df.empty:
                combined_results.append(results_df)
        
        if not combined_results:
            st.info("Add products to the deal matrices to see detailed results.")
            return
        
        all_df = pd.concat(combined_results, ignore_index=True)
        
        display_columns = [
            'material_code',
            'tx_variant',
            'region_classification',
            'volume_eur',
            'tx_count',
            'proposed_variable_pct',
            'proposed_fixed_eur',
            'actual_revenue',
            'target_revenue',
            'total_cost',
            'actual_margin',
            'target_margin',
            'realization_pct',
        ]
        
        available_columns = [col for col in display_columns if col in all_df.columns]
        display_df = all_df[available_columns]
        
        column_config = {
            "material_code": st.column_config.TextColumn("Product", width="medium"),
            "tx_variant": st.column_config.TextColumn("Variant", width="small"),
            "region_classification": st.column_config.TextColumn("Region", width="small"),
            "volume_eur": st.column_config.NumberColumn("Volume", format="€%.0f"),
            "tx_count": st.column_config.NumberColumn("Tx Count", format="%d"),
            "proposed_variable_pct": st.column_config.NumberColumn("Prop. Var %", format="%.4f%%"),
            "proposed_fixed_eur": st.column_config.NumberColumn("Prop. Fixed", format="€%.4f"),
            "actual_revenue": st.column_config.NumberColumn("Actual Rev", format="€%.2f"),
            "target_revenue": st.column_config.NumberColumn("Target Rev", format="€%.2f"),
            "total_cost": st.column_config.NumberColumn("Cost", format="€%.2f"),
            "actual_margin": st.column_config.NumberColumn("Actual Margin", format="€%.2f"),
            "target_margin": st.column_config.NumberColumn("Target Margin", format="€%.2f"),
            "realization_pct": st.column_config.NumberColumn("Realization %", format="%.1f%%"),
        }
        
        st.dataframe(
            display_df,
            column_config=column_config,
            width="stretch",
            hide_index=True
        )


def render_sidebar_settings(default_date: Any) -> Dict[str, Any]:
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
        help="Select the effective date for this deal"
    )
    
    return {
        'merchant_name': merchant_name,
        'deal_date': deal_date,
    }


def render_admin_settings() -> Dict[str, Any]:
    """
    Render admin settings expander with file upload options.
    Returns uploaded files if any.
    """
    with st.sidebar.expander("Admin Settings"):
        st.caption("Upload custom CSV file to override default pricing data")
        
        pricing_file = st.file_uploader(
            "Upload Pricing CSV",
            type=['csv'],
            key="pricing_uploader",
            help="CSV with columns: material_code, tx_variant, region_classification, cost_variable, cost_fixed, target_variable, target_fixed"
        )
        
        if pricing_file is not None:
            st.success("Custom pricing data uploaded!")
        
        return {
            'pricing_file': pricing_file,
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


def render_realization_breakdown(all_results: Dict[str, pd.DataFrame]) -> None:
    """
    Render a breakdown of realization by product line.
    """
    with st.container(border=True):
        st.subheader("Realization by Product")
        
        product_labels = {
            'AcquiringService': 'Acquiring',
            'ProcessingService': 'Processing',
            'RevenueProtectService': 'Revenue Protect'
        }
        
        cols = st.columns(len(all_results))
        
        for idx, (material_code, results_df) in enumerate(all_results.items()):
            if results_df.empty:
                continue
            
            total_actual_margin = results_df['actual_margin'].sum()
            total_target_margin = results_df['target_margin'].sum()
            
            if total_target_margin > 0:
                realization = (total_actual_margin / total_target_margin) * 100
            else:
                realization = 100.0 if total_actual_margin >= 0 else 0.0
            
            color = "#d32f2f" if realization < 95 else "#388e3c"
            
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f5f5f5;
                        border-radius: 8px;
                        padding: 12px;
                        text-align: center;
                        margin-bottom: 8px;
                    ">
                        <p style="color: #666; margin: 0; font-size: 12px;">{product_labels.get(material_code, material_code)}</p>
                        <p style="color: {color}; margin: 4px 0; font-size: 24px; font-weight: 600;">{realization:.1f}%</p>
                        <p style="color: #666; margin: 0; font-size: 11px;">Margin: €{total_actual_margin:,.0f}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


def render_export_section(
    all_results: Dict[str, pd.DataFrame],
    metrics: Dict[str, Any],
    merchant_name: str,
    deal_date: Any
) -> None:
    """
    Render data export section with download buttons for CSV.
    """
    with st.container(border=True):
        st.subheader("Export Deal Analysis")
        
        combined_results = []
        for material_code, results_df in all_results.items():
            if not results_df.empty:
                combined_results.append(results_df)
        
        if not combined_results:
            st.info("Add products to the deal matrices to enable export.")
            return
        
        all_df = pd.concat(combined_results, ignore_index=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_df = all_df.copy()
            export_df['merchant_name'] = merchant_name
            export_df['deal_date'] = str(deal_date)
            export_df['export_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            csv_buffer = io.StringIO()
            export_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="Download Detailed Results (CSV)",
                data=csv_data,
                file_name=f"deal_analysis_{merchant_name.replace(' ', '_')}_{deal_date}.csv",
                mime="text/csv",
                key="download_detailed"
            )
        
        with col2:
            summary_data = {
                'Metric': [
                    'Merchant Name',
                    'Deal Date',
                    'Total Deal Value (EUR)',
                    'Total Actual Revenue (EUR)',
                    'Total Target Revenue (EUR)',
                    'Total Cost (EUR)',
                    'Total Actual Margin (EUR)',
                    'Total Target Margin (EUR)',
                    'Global Realization (%)',
                    'Number of Products'
                ],
                'Value': [
                    merchant_name,
                    str(deal_date),
                    f"€{metrics['total_deal_value']:,.2f}",
                    f"€{metrics['total_actual_revenue']:,.2f}",
                    f"€{metrics['total_target_revenue']:,.2f}",
                    f"€{metrics['total_cost']:,.2f}",
                    f"€{metrics['total_actual_margin']:,.2f}",
                    f"€{metrics['total_target_margin']:,.2f}",
                    f"{metrics['global_realization_pct']:.1f}%",
                    str(metrics['row_count'])
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            
            csv_buffer = io.StringIO()
            summary_df.to_csv(csv_buffer, index=False)
            summary_csv = csv_buffer.getvalue()
            
            st.download_button(
                label="Download Summary (CSV)",
                data=summary_csv,
                file_name=f"deal_summary_{merchant_name.replace(' ', '_')}_{deal_date}.csv",
                mime="text/csv",
                key="download_summary"
            )


def render_historical_comparison(saved_deals: List[Dict[str, Any]]) -> None:
    """
    Render historical deal comparison view with trend charts.
    """
    with st.container(border=True):
        st.subheader("Historical Deal Comparison")
        
        if not saved_deals or len(saved_deals) == 0:
            st.info("Save deals to compare them over time. Use 'Save Current Deal' button below.")
            return
        
        history_df = pd.DataFrame([
            {
                'Deal Name': deal['name'],
                'Merchant': deal['merchant_name'],
                'Date': deal['deal_date'],
                'Total Value': deal['metrics']['total_deal_value'],
                'Actual Margin': deal['metrics']['total_actual_margin'],
                'Target Margin': deal['metrics']['total_target_margin'],
                'Realization %': deal['metrics']['global_realization_pct'],
                'Products': deal['metrics']['row_count'],
                'Saved At': deal['saved_at']
            }
            for deal in saved_deals
        ])
        
        st.dataframe(
            history_df,
            column_config={
                "Deal Name": st.column_config.TextColumn("Deal Name", width="medium"),
                "Merchant": st.column_config.TextColumn("Merchant", width="small"),
                "Date": st.column_config.TextColumn("Date", width="small"),
                "Total Value": st.column_config.NumberColumn("Total Value", format="€%.0f"),
                "Actual Margin": st.column_config.NumberColumn("Actual Margin", format="€%.2f"),
                "Target Margin": st.column_config.NumberColumn("Target Margin", format="€%.2f"),
                "Realization %": st.column_config.NumberColumn("Realization", format="%.1f%%"),
                "Products": st.column_config.NumberColumn("Products", format="%d"),
                "Saved At": st.column_config.TextColumn("Saved At", width="medium"),
            },
            width="stretch",
            hide_index=True
        )
        
        if len(saved_deals) >= 2:
            st.markdown("#### Realization Trend")
            
            trend_data = pd.DataFrame([
                {
                    'Deal': deal['name'],
                    'Realization': deal['metrics']['global_realization_pct'],
                    'Actual Margin': deal['metrics']['total_actual_margin']
                }
                for deal in saved_deals
            ])
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=list(range(len(trend_data))),
                y=trend_data['Realization'],
                mode='lines+markers',
                name='Realization %',
                line=dict(color='#1976D2', width=3),
                marker=dict(size=10)
            ))
            
            fig.add_hline(y=95, line_dash="dash", line_color="red", 
                         annotation_text="95% Target", annotation_position="right")
            
            fig.update_layout(
                xaxis_title='Deal Sequence',
                yaxis_title='Realization %',
                height=300,
                margin=dict(t=30, b=30),
                xaxis=dict(tickmode='array', tickvals=list(range(len(trend_data))),
                          ticktext=trend_data['Deal'].tolist())
            )
            
            st.plotly_chart(fig, width="stretch")


def render_drill_down_analysis(all_results: Dict[str, pd.DataFrame]) -> None:
    """
    Render drill-down analysis by product line and transaction variant.
    """
    with st.container(border=True):
        st.subheader("Drill-Down Analysis")
        
        combined_results = []
        for material_code, results_df in all_results.items():
            if not results_df.empty:
                combined_results.append(results_df)
        
        if not combined_results:
            st.info("Add products to see drill-down analysis.")
            return
        
        all_df = pd.concat(combined_results, ignore_index=True)
        
        tab1, tab2 = st.tabs(["By Product Line", "By Transaction Variant"])
        
        with tab1:
            product_grouped = all_df.groupby('material_code').agg({
                'volume_eur': 'sum',
                'tx_count': 'sum',
                'actual_revenue': 'sum',
                'target_revenue': 'sum',
                'total_cost': 'sum',
                'actual_margin': 'sum',
                'target_margin': 'sum'
            }).reset_index()
            
            product_grouped['realization_pct'] = (
                product_grouped['actual_margin'] / product_grouped['target_margin'] * 100
            ).round(1)
            product_grouped['margin_pct'] = (
                product_grouped['actual_margin'] / product_grouped['actual_revenue'] * 100
            ).round(1)
            
            fig_product = go.Figure()
            
            fig_product.add_trace(go.Bar(
                name='Actual Margin',
                x=product_grouped['material_code'],
                y=product_grouped['actual_margin'],
                marker_color='#4CAF50',
                text=product_grouped['actual_margin'].apply(lambda x: f'€{x:,.0f}'),
                textposition='outside'
            ))
            
            fig_product.add_trace(go.Bar(
                name='Target Margin',
                x=product_grouped['material_code'],
                y=product_grouped['target_margin'],
                marker_color='#1976D2',
                text=product_grouped['target_margin'].apply(lambda x: f'€{x:,.0f}'),
                textposition='outside'
            ))
            
            fig_product.add_trace(go.Bar(
                name='Total Cost',
                x=product_grouped['material_code'],
                y=product_grouped['total_cost'],
                marker_color='#FF5722',
                text=product_grouped['total_cost'].apply(lambda x: f'€{x:,.0f}'),
                textposition='outside'
            ))
            
            fig_product.update_layout(
                barmode='group',
                xaxis_title='Product Line',
                yaxis_title='Amount (EUR)',
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig_product, width="stretch")
            
            st.markdown("##### Product Metrics")
            st.dataframe(
                product_grouped[['material_code', 'volume_eur', 'tx_count', 'actual_margin', 
                                'target_margin', 'realization_pct']],
                column_config={
                    "material_code": st.column_config.TextColumn("Product"),
                    "volume_eur": st.column_config.NumberColumn("Volume", format="€%.0f"),
                    "tx_count": st.column_config.NumberColumn("Tx Count", format="%d"),
                    "actual_margin": st.column_config.NumberColumn("Actual Margin", format="€%.2f"),
                    "target_margin": st.column_config.NumberColumn("Target Margin", format="€%.2f"),
                    "realization_pct": st.column_config.NumberColumn("Realization", format="%.1f%%"),
                },
                width="stretch",
                hide_index=True
            )
        
        with tab2:
            variant_grouped = all_df.groupby('tx_variant').agg({
                'volume_eur': 'sum',
                'tx_count': 'sum',
                'actual_revenue': 'sum',
                'actual_margin': 'sum',
                'target_margin': 'sum'
            }).reset_index()
            
            variant_grouped['realization_pct'] = (
                variant_grouped['actual_margin'] / variant_grouped['target_margin'] * 100
            ).round(1)
            
            fig_variant = px.pie(
                variant_grouped,
                values='actual_margin',
                names='tx_variant',
                title='Margin by Transaction Variant',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            
            fig_variant.update_traces(textposition='inside', textinfo='percent+label')
            fig_variant.update_layout(height=350)
            
            st.plotly_chart(fig_variant, width="stretch")
            
            st.markdown("##### Variant Metrics")
            st.dataframe(
                variant_grouped[['tx_variant', 'volume_eur', 'tx_count', 'actual_margin', 
                                'target_margin', 'realization_pct']],
                column_config={
                    "tx_variant": st.column_config.TextColumn("Variant"),
                    "volume_eur": st.column_config.NumberColumn("Volume", format="€%.0f"),
                    "tx_count": st.column_config.NumberColumn("Tx Count", format="%d"),
                    "actual_margin": st.column_config.NumberColumn("Actual Margin", format="€%.2f"),
                    "target_margin": st.column_config.NumberColumn("Target Margin", format="€%.2f"),
                    "realization_pct": st.column_config.NumberColumn("Realization", format="%.1f%%"),
                },
                width="stretch",
                hide_index=True
            )


def render_scenario_comparison(scenarios: List[Dict[str, Any]]) -> None:
    """
    Render side-by-side scenario comparison for what-if analysis.
    """
    with st.container(border=True):
        st.subheader("Scenario Comparison")
        
        if not scenarios or len(scenarios) < 2:
            st.info("Save at least 2 scenarios to compare. Use 'Save as Scenario' button to save the current deal configuration.")
            return
        
        scenario_names = [s['name'] for s in scenarios]
        
        col1, col2 = st.columns(2)
        
        with col1:
            scenario_a_name = st.selectbox(
                "Scenario A",
                options=scenario_names,
                index=0,
                key="scenario_a_select"
            )
        
        with col2:
            default_b_idx = min(1, len(scenario_names) - 1)
            scenario_b_name = st.selectbox(
                "Scenario B",
                options=scenario_names,
                index=default_b_idx,
                key="scenario_b_select"
            )
        
        scenario_a = next((s for s in scenarios if s['name'] == scenario_a_name), None)
        scenario_b = next((s for s in scenarios if s['name'] == scenario_b_name), None)
        
        if scenario_a and scenario_b:
            metrics_a = scenario_a['metrics']
            metrics_b = scenario_b['metrics']
            
            comparison_data = {
                'Metric': [
                    'Total Deal Value',
                    'Actual Margin',
                    'Target Margin',
                    'Total Cost',
                    'Realization %',
                    'Product Count'
                ],
                scenario_a_name: [
                    f"€{metrics_a['total_deal_value']:,.0f}",
                    f"€{metrics_a['total_actual_margin']:,.2f}",
                    f"€{metrics_a['total_target_margin']:,.2f}",
                    f"€{metrics_a['total_cost']:,.2f}",
                    f"{metrics_a['global_realization_pct']:.1f}%",
                    str(metrics_a['row_count'])
                ],
                scenario_b_name: [
                    f"€{metrics_b['total_deal_value']:,.0f}",
                    f"€{metrics_b['total_actual_margin']:,.2f}",
                    f"€{metrics_b['total_target_margin']:,.2f}",
                    f"€{metrics_b['total_cost']:,.2f}",
                    f"{metrics_b['global_realization_pct']:.1f}%",
                    str(metrics_b['row_count'])
                ],
                'Difference': [
                    f"€{metrics_b['total_deal_value'] - metrics_a['total_deal_value']:+,.0f}",
                    f"€{metrics_b['total_actual_margin'] - metrics_a['total_actual_margin']:+,.2f}",
                    f"€{metrics_b['total_target_margin'] - metrics_a['total_target_margin']:+,.2f}",
                    f"€{metrics_b['total_cost'] - metrics_a['total_cost']:+,.2f}",
                    f"{metrics_b['global_realization_pct'] - metrics_a['global_realization_pct']:+.1f}pp",
                    f"{metrics_b['row_count'] - metrics_a['row_count']:+d}"
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            
            st.dataframe(
                comparison_df,
                width="stretch",
                hide_index=True
            )
            
            fig = go.Figure()
            
            metrics_for_chart = ['Total Deal Value', 'Actual Margin', 'Target Margin']
            values_a = [
                metrics_a['total_deal_value'],
                metrics_a['total_actual_margin'],
                metrics_a['total_target_margin']
            ]
            values_b = [
                metrics_b['total_deal_value'],
                metrics_b['total_actual_margin'],
                metrics_b['total_target_margin']
            ]
            
            fig.add_trace(go.Bar(
                name=scenario_a_name,
                x=metrics_for_chart,
                y=values_a,
                marker_color='#1976D2',
                text=[f'€{v:,.0f}' for v in values_a],
                textposition='outside'
            ))
            
            fig.add_trace(go.Bar(
                name=scenario_b_name,
                x=metrics_for_chart,
                y=values_b,
                marker_color='#4CAF50',
                text=[f'€{v:,.0f}' for v in values_b],
                textposition='outside'
            ))
            
            fig.update_layout(
                barmode='group',
                xaxis_title='Metric',
                yaxis_title='Amount (EUR)',
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, width="stretch")


def render_save_deal_controls(
    merchant_name: str,
    deal_date: Any,
    metrics: Dict[str, Any],
    all_results: Dict[str, pd.DataFrame]
) -> Optional[Dict[str, Any]]:
    """
    Render controls for saving deals/scenarios.
    Returns deal data if save button is clicked.
    """
    with st.container(border=True):
        st.subheader("Save Deal / Scenario")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            deal_name = st.text_input(
                "Deal/Scenario Name",
                value=f"{merchant_name} - {deal_date}",
                key="save_deal_name"
            )
        
        with col2:
            save_as_deal = st.button(
                "Save as Deal",
                key="save_deal_btn",
                type="primary"
            )
        
        with col3:
            save_as_scenario = st.button(
                "Save as Scenario",
                key="save_scenario_btn"
            )
        
        if save_as_deal or save_as_scenario:
            combined_results = []
            for material_code, results_df in all_results.items():
                if not results_df.empty:
                    combined_results.append(results_df)
            
            if combined_results:
                all_df = pd.concat(combined_results, ignore_index=True)
                results_records = all_df.to_dict('records')
            else:
                results_records = []
            
            return {
                'name': deal_name,
                'merchant_name': merchant_name,
                'deal_date': str(deal_date),
                'metrics': metrics,
                'results': results_records,
                'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'deal' if save_as_deal else 'scenario'
            }
        
        return None
