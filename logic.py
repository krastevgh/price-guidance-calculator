"""
Logic Module for Commercial Pricing Guidance & Realization.
Contains pure Python functions for calculations, lookups, and business rules.
"""

import pandas as pd
from datetime import date
from typing import Dict, List, Optional, Tuple, Any


def calculate_deal_realization(
    deal_inputs_df: pd.DataFrame,
    guidance_df: pd.DataFrame,
    costs_df: pd.DataFrame,
    deal_date: date,
    classification: str
) -> pd.DataFrame:
    """
    Calculate deal realization metrics for all input rows.
    
    Args:
        deal_inputs_df: User's deal input with proposed pricing
        guidance_df: Commercial guidance reference data
        costs_df: Cost base reference data
        deal_date: The deal date for validity filtering
        classification: Price guidance classification (region)
    
    Returns:
        DataFrame with calculated metrics per row
    """
    results = []
    
    date_filtered_guidance = filter_guidance_by_date(guidance_df, deal_date)
    
    for _, row in deal_inputs_df.iterrows():
        result = calculate_single_row_realization(
            row=row,
            guidance_df=date_filtered_guidance,
            costs_df=costs_df,
            classification=classification
        )
        results.append(result)
    
    return pd.DataFrame(results)


def filter_guidance_by_date(guidance_df: pd.DataFrame, deal_date: date) -> pd.DataFrame:
    """
    Filter guidance data to only include rows valid for the given date.
    """
    deal_timestamp = pd.Timestamp(deal_date)
    
    mask = (
        (guidance_df['valid_from'] <= deal_timestamp) &
        (guidance_df['valid_to'] >= deal_timestamp)
    )
    
    return guidance_df[mask].copy()


def lookup_guidance(
    guidance_df: pd.DataFrame,
    material_code: str,
    tx_variant: str,
    classification: str,
    volume: float
) -> Optional[Dict[str, Any]]:
    """
    Find the specific guidance row matching the criteria.
    """
    mask = (
        (guidance_df['material_code'] == material_code) &
        (guidance_df['tx_variant'] == tx_variant) &
        (guidance_df['price_guidance_classification'] == classification) &
        (guidance_df['min_vol_eur'] <= volume) &
        (guidance_df['max_vol_eur'] > volume)
    )
    
    matched = guidance_df[mask]
    
    if matched.empty:
        return None
    
    return matched.iloc[0].to_dict()


def lookup_costs(
    costs_df: pd.DataFrame,
    material_code: str,
    tx_variant: str,
    classification: str
) -> Optional[Dict[str, Any]]:
    """
    Find the cost structure for the given product and region.
    """
    region_mapping = {
        'Europe Domestic': 'Europe Domestic',
        'NorthAmerica Domestic': 'NorthAmerica Domestic',
        'Global': 'Global',
    }
    
    region = region_mapping.get(classification, 'Global')
    
    mask = (
        (costs_df['material_code'] == material_code) &
        (costs_df['tx_variant'] == tx_variant) &
        (costs_df['region_classification'] == region)
    )
    
    matched = costs_df[mask]
    
    if matched.empty:
        return None
    
    return matched.iloc[0].to_dict()


def calculate_single_row_realization(
    row: pd.Series,
    guidance_df: pd.DataFrame,
    costs_df: pd.DataFrame,
    classification: str
) -> Dict[str, Any]:
    """
    Calculate realization metrics for a single deal row.
    """
    material_code = row['material_code']
    tx_variant = row['tx_variant']
    volume = float(row['volume_eur'])
    tx_count = int(row['tx_count'])
    proposed_var_pct = float(row['proposed_variable_pct'])
    proposed_fixed = float(row['proposed_fixed_eur'])
    
    proposed_var = proposed_var_pct / 100.0
    
    if material_code == 'ProcessingService':
        proposed_var = 0.0
    
    guidance = lookup_guidance(
        guidance_df, material_code, tx_variant, classification, volume
    )
    
    costs = lookup_costs(
        costs_df, material_code, tx_variant, classification
    )
    
    result = {
        'material_code': material_code,
        'tx_variant': tx_variant,
        'volume_eur': volume,
        'tx_count': tx_count,
        'proposed_variable_pct': proposed_var_pct,
        'proposed_fixed_eur': proposed_fixed,
        'effective_variable': proposed_var,
    }
    
    if guidance is None:
        result.update({
            'target_variable': None,
            'target_fixed': None,
            'actual_revenue': calculate_revenue(volume, proposed_var, tx_count, proposed_fixed),
            'target_revenue': None,
            'realization_pct': None,
            'guidance_status': 'No Guidance Found',
        })
    else:
        target_var = float(guidance['advised_fee_variable'])
        target_fixed = float(guidance['advised_fee_fixed_eur'])
        
        if material_code == 'ProcessingService':
            target_var = 0.0
        
        actual_revenue = calculate_revenue(volume, proposed_var, tx_count, proposed_fixed)
        target_revenue = calculate_revenue(volume, target_var, tx_count, target_fixed)
        
        if target_revenue > 0:
            realization_pct = (actual_revenue / target_revenue) * 100
        else:
            realization_pct = 0.0
        
        result.update({
            'target_variable': target_var,
            'target_fixed': target_fixed,
            'actual_revenue': actual_revenue,
            'target_revenue': target_revenue,
            'realization_pct': realization_pct,
            'guidance_status': 'Found',
        })
    
    if costs is None:
        result.update({
            'cost_variable': 0.0,
            'cost_fixed': 0.0,
            'total_cost': 0.0,
            'actual_margin': result.get('actual_revenue', 0.0),
            'cost_status': 'No Costs Found',
        })
    else:
        cost_var = float(costs['cost_variable'])
        cost_fixed = float(costs['cost_fixed_eur'])
        
        total_cost = calculate_revenue(volume, cost_var, tx_count, cost_fixed)
        actual_margin = result.get('actual_revenue', 0.0) - total_cost
        
        result.update({
            'cost_variable': cost_var,
            'cost_fixed': cost_fixed,
            'total_cost': total_cost,
            'actual_margin': actual_margin,
            'cost_status': 'Found',
        })
    
    return result


def calculate_revenue(
    volume: float,
    variable_rate: float,
    tx_count: int,
    fixed_fee: float
) -> float:
    """
    Calculate revenue/cost using the formula:
    Revenue = (Volume * Variable Rate) + (Tx Count * Fixed Fee)
    """
    return (volume * variable_rate) + (tx_count * fixed_fee)


def calculate_tx_count_from_atv(volume: float, atv: float) -> int:
    """
    Calculate transaction count from volume and average transaction value.
    """
    if atv <= 0:
        return 0
    return max(1, int(volume / atv))


def aggregate_deal_metrics(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregate metrics across all deal rows.
    """
    if results_df.empty:
        return {
            'total_deal_value': 0.0,
            'total_actual_revenue': 0.0,
            'total_target_revenue': 0.0,
            'total_cost': 0.0,
            'total_margin': 0.0,
            'global_realization_pct': 0.0,
            'row_count': 0,
        }
    
    total_volume = results_df['volume_eur'].sum()
    total_actual_revenue = results_df['actual_revenue'].sum()
    
    valid_target = results_df[results_df['target_revenue'].notna()]
    total_target_revenue = valid_target['target_revenue'].sum() if not valid_target.empty else 0.0
    
    total_cost = results_df['total_cost'].sum()
    total_margin = results_df['actual_margin'].sum()
    
    if total_target_revenue > 0:
        global_realization_pct = (total_actual_revenue / total_target_revenue) * 100
    else:
        global_realization_pct = 0.0
    
    return {
        'total_deal_value': total_volume,
        'total_actual_revenue': total_actual_revenue,
        'total_target_revenue': total_target_revenue,
        'total_cost': total_cost,
        'total_margin': total_margin,
        'global_realization_pct': global_realization_pct,
        'row_count': len(results_df),
    }


def validate_deal_inputs(deal_inputs_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate deal inputs and return list of any errors.
    """
    errors = []
    
    required_columns = [
        'material_code', 'tx_variant', 'volume_eur',
        'tx_count', 'proposed_variable_pct', 'proposed_fixed_eur'
    ]
    
    missing_cols = set(required_columns) - set(deal_inputs_df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors
    
    for idx, row in deal_inputs_df.iterrows():
        if row['volume_eur'] < 0:
            errors.append(f"Row {idx + 1}: Volume cannot be negative")
        if row['tx_count'] < 0:
            errors.append(f"Row {idx + 1}: Transaction count cannot be negative")
        if row['proposed_variable_pct'] < 0:
            errors.append(f"Row {idx + 1}: Variable fee cannot be negative")
        if row['proposed_fixed_eur'] < 0:
            errors.append(f"Row {idx + 1}: Fixed fee cannot be negative")
    
    return len(errors) == 0, errors


def get_realization_status(realization_pct: Optional[float]) -> str:
    """
    Determine the status based on realization percentage.
    """
    if realization_pct is None:
        return "unknown"
    elif realization_pct >= 100:
        return "above_target"
    elif realization_pct >= 95:
        return "on_target"
    elif realization_pct >= 80:
        return "below_target"
    else:
        return "critical"


def format_currency(value: float, currency: str = "EUR") -> str:
    """
    Format a numeric value as currency.
    """
    if currency == "EUR":
        return f"€{value:,.2f}"
    return f"{value:,.2f} {currency}"


def format_percentage(value: float) -> str:
    """
    Format a numeric value as percentage.
    """
    return f"{value:.2f}%"
