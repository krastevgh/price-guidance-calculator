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
            width="stretch",
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
        
        st.plotly_chart(fig, width="stretch")


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
            width="stretch",
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
            col_idx = int(idx) % 3
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


def render_export_section(
    results_df: pd.DataFrame,
    metrics: Dict[str, Any],
    merchant_name: str,
    deal_date: Any
) -> None:
    """
    Render data export section with download buttons for CSV.
    """
    with st.container(border=True):
        st.subheader("Export Deal Analysis")
        
        if results_df.empty:
            st.info("Add products to the deal matrix to enable export.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_df = results_df.copy()
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
                    'Total Margin (EUR)',
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
                    f"€{metrics['total_margin']:,.2f}",
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
                'Margin': deal['metrics']['total_margin'],
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
                "Margin": st.column_config.NumberColumn("Margin", format="€%.2f"),
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
                    'Margin': deal['metrics']['total_margin']
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


def render_drill_down_analysis(results_df: pd.DataFrame) -> None:
    """
    Render drill-down analysis by product line and transaction variant.
    """
    with st.container(border=True):
        st.subheader("Drill-Down Analysis")
        
        if results_df.empty:
            st.info("Add products to see drill-down analysis.")
            return
        
        valid_results = results_df[results_df['target_revenue'].notna()].copy()
        
        if valid_results.empty:
            st.warning("No guidance available for drill-down analysis.")
            return
        
        tab1, tab2 = st.tabs(["By Product Line", "By Transaction Variant"])
        
        with tab1:
            product_grouped = valid_results.groupby('material_code').agg({
                'volume_eur': 'sum',
                'tx_count': 'sum',
                'actual_revenue': 'sum',
                'target_revenue': 'sum',
                'total_cost': 'sum',
                'actual_margin': 'sum'
            }).reset_index()
            
            product_grouped['realization_pct'] = (
                product_grouped['actual_revenue'] / product_grouped['target_revenue'] * 100
            ).round(1)
            product_grouped['margin_pct'] = (
                product_grouped['actual_margin'] / product_grouped['actual_revenue'] * 100
            ).round(1)
            
            fig_product = go.Figure()
            
            fig_product.add_trace(go.Bar(
                name='Actual Revenue',
                x=product_grouped['material_code'],
                y=product_grouped['actual_revenue'],
                marker_color='#4CAF50',
                text=product_grouped['actual_revenue'].apply(lambda x: f'€{x:,.0f}'),
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
            
            fig_product.add_trace(go.Bar(
                name='Margin',
                x=product_grouped['material_code'],
                y=product_grouped['actual_margin'],
                marker_color='#2196F3',
                text=product_grouped['actual_margin'].apply(lambda x: f'€{x:,.0f}'),
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
                product_grouped[['material_code', 'volume_eur', 'tx_count', 'actual_revenue', 
                                'actual_margin', 'realization_pct', 'margin_pct']],
                column_config={
                    "material_code": st.column_config.TextColumn("Product"),
                    "volume_eur": st.column_config.NumberColumn("Volume", format="€%.0f"),
                    "tx_count": st.column_config.NumberColumn("Tx Count", format="%d"),
                    "actual_revenue": st.column_config.NumberColumn("Revenue", format="€%.2f"),
                    "actual_margin": st.column_config.NumberColumn("Margin", format="€%.2f"),
                    "realization_pct": st.column_config.NumberColumn("Realization", format="%.1f%%"),
                    "margin_pct": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                },
                width="stretch",
                hide_index=True
            )
        
        with tab2:
            variant_grouped = valid_results.groupby('tx_variant').agg({
                'volume_eur': 'sum',
                'tx_count': 'sum',
                'actual_revenue': 'sum',
                'target_revenue': 'sum',
                'total_cost': 'sum',
                'actual_margin': 'sum'
            }).reset_index()
            
            variant_grouped['realization_pct'] = (
                variant_grouped['actual_revenue'] / variant_grouped['target_revenue'] * 100
            ).round(1)
            
            fig_variant = px.pie(
                variant_grouped,
                values='actual_revenue',
                names='tx_variant',
                title='Revenue by Transaction Variant',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            
            fig_variant.update_traces(textposition='inside', textinfo='percent+label')
            fig_variant.update_layout(height=350)
            
            st.plotly_chart(fig_variant, width="stretch")
            
            st.markdown("##### Variant Metrics")
            st.dataframe(
                variant_grouped[['tx_variant', 'volume_eur', 'tx_count', 'actual_revenue', 
                                'actual_margin', 'realization_pct']],
                column_config={
                    "tx_variant": st.column_config.TextColumn("Variant"),
                    "volume_eur": st.column_config.NumberColumn("Volume", format="€%.0f"),
                    "tx_count": st.column_config.NumberColumn("Tx Count", format="%d"),
                    "actual_revenue": st.column_config.NumberColumn("Revenue", format="€%.2f"),
                    "actual_margin": st.column_config.NumberColumn("Margin", format="€%.2f"),
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
                    'Actual Revenue',
                    'Target Revenue',
                    'Total Cost',
                    'Total Margin',
                    'Realization %',
                    'Product Count'
                ],
                scenario_a_name: [
                    f"€{metrics_a['total_deal_value']:,.0f}",
                    f"€{metrics_a['total_actual_revenue']:,.2f}",
                    f"€{metrics_a['total_target_revenue']:,.2f}",
                    f"€{metrics_a['total_cost']:,.2f}",
                    f"€{metrics_a['total_margin']:,.2f}",
                    f"{metrics_a['global_realization_pct']:.1f}%",
                    str(metrics_a['row_count'])
                ],
                scenario_b_name: [
                    f"€{metrics_b['total_deal_value']:,.0f}",
                    f"€{metrics_b['total_actual_revenue']:,.2f}",
                    f"€{metrics_b['total_target_revenue']:,.2f}",
                    f"€{metrics_b['total_cost']:,.2f}",
                    f"€{metrics_b['total_margin']:,.2f}",
                    f"{metrics_b['global_realization_pct']:.1f}%",
                    str(metrics_b['row_count'])
                ],
                'Difference': [
                    f"€{metrics_b['total_deal_value'] - metrics_a['total_deal_value']:+,.0f}",
                    f"€{metrics_b['total_actual_revenue'] - metrics_a['total_actual_revenue']:+,.2f}",
                    f"€{metrics_b['total_target_revenue'] - metrics_a['total_target_revenue']:+,.2f}",
                    f"€{metrics_b['total_cost'] - metrics_a['total_cost']:+,.2f}",
                    f"€{metrics_b['total_margin'] - metrics_a['total_margin']:+,.2f}",
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
            
            metrics_for_chart = ['Total Deal Value', 'Actual Revenue', 'Total Margin']
            values_a = [
                metrics_a['total_deal_value'],
                metrics_a['total_actual_revenue'],
                metrics_a['total_margin']
            ]
            values_b = [
                metrics_b['total_deal_value'],
                metrics_b['total_actual_revenue'],
                metrics_b['total_margin']
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
    results_df: pd.DataFrame
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
            return {
                'name': deal_name,
                'merchant_name': merchant_name,
                'deal_date': str(deal_date),
                'metrics': metrics,
                'results': results_df.to_dict('records'),
                'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'deal' if save_as_deal else 'scenario'
            }
        
        return None
