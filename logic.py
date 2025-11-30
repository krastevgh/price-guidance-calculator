"""
Logic Module for Commercial Pricing Guidance & Realization.
Contains pure Python functions for calculations, lookups, and business rules.
"""

import pandas as pd
from typing import Dict, List, Tuple, Any
from data import lookup_pricing


def calculate_deal_realization(
    deal_inputs_df: pd.DataFrame,
    pricing_df: pd.DataFrame,
    material_code: str
) -> pd.DataFrame:
    """
    Calculate deal realization metrics for all input rows of a product.
    
    New calculation logic:
    - Actual Revenue = (Volume * proposed_var) + (Tx * proposed_fixed)
    - Target Revenue = (Volume * target_var) + (Tx * target_fixed)
    - Cost = (Volume * cost_var) + (Tx * cost_fixed)
    - Actual Margin = Actual Revenue - Cost
    - Target Margin = Target Revenue - Cost
    - Realization % = (Actual Margin / Target Margin) * 100
    """
    results = []
    
    for _, row in deal_inputs_df.iterrows():
        result = calculate_single_row_realization(
            row=row,
            pricing_df=pricing_df,
            material_code=material_code
        )
        results.append(result)
    
    return pd.DataFrame(results)


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float, handling NaN and empty strings."""
    if pd.isna(value) or value == '' or value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int, handling NaN and empty strings."""
    if pd.isna(value) or value == '' or value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def calculate_single_row_realization(
    row: pd.Series,
    pricing_df: pd.DataFrame,
    material_code: str
) -> Dict[str, Any]:
    """
    Calculate realization metrics for a single deal row.
    Handles NaN/blank values gracefully.
    """
    tx_variant = str(row.get('tx_variant', '')).strip()
    classification = str(row.get('region_classification', '')).strip()
    volume = safe_float(row.get('volume_eur', 0), 0.0)
    atv = safe_float(row.get('atv', 100), 100.0)
    tx_count = safe_int(row.get('tx_count', 1), 1)
    
    target_var_pct = safe_float(row.get('target_variable_pct', 0), 0.0)
    target_fixed = safe_float(row.get('target_fixed_eur', 0), 0.0)
    proposed_var_pct = safe_float(row.get('proposed_variable_pct', 0), 0.0)
    proposed_fixed = safe_float(row.get('proposed_fixed_eur', 0), 0.0)
    
    target_var = target_var_pct / 100.0
    proposed_var = proposed_var_pct / 100.0
    
    pricing = lookup_pricing(pricing_df, material_code, tx_variant, classification)
    
    cost_var = pricing['cost_variable']
    cost_fixed = pricing['cost_fixed']
    
    actual_revenue = calculate_revenue(volume, proposed_var, tx_count, proposed_fixed)
    target_revenue = calculate_revenue(volume, target_var, tx_count, target_fixed)
    total_cost = calculate_revenue(volume, cost_var, tx_count, cost_fixed)
    
    actual_margin = actual_revenue - total_cost
    target_margin = target_revenue - total_cost
    
    if target_margin > 0:
        realization_pct = (actual_margin / target_margin) * 100
    elif target_margin == 0 and actual_margin >= 0:
        realization_pct = 100.0
    else:
        realization_pct = 0.0
    
    result = {
        'material_code': material_code,
        'tx_variant': tx_variant,
        'region_classification': classification,
        'volume_eur': volume,
        'atv': atv,
        'tx_count': tx_count,
        'target_variable_pct': target_var_pct,
        'target_fixed_eur': target_fixed,
        'proposed_variable_pct': proposed_var_pct,
        'proposed_fixed_eur': proposed_fixed,
        'cost_variable': cost_var,
        'cost_fixed': cost_fixed,
        'actual_revenue': actual_revenue,
        'target_revenue': target_revenue,
        'total_cost': total_cost,
        'actual_margin': actual_margin,
        'target_margin': target_margin,
        'realization_pct': realization_pct,
        'pricing_status': 'Found' if pricing['found'] else 'No Pricing Found',
    }
    
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
            'total_actual_margin': 0.0,
            'total_target_margin': 0.0,
            'global_realization_pct': 0.0,
            'row_count': 0,
        }
    
    total_volume = results_df['volume_eur'].sum()
    total_actual_revenue = results_df['actual_revenue'].sum()
    total_target_revenue = results_df['target_revenue'].sum()
    total_cost = results_df['total_cost'].sum()
    total_actual_margin = results_df['actual_margin'].sum()
    total_target_margin = results_df['target_margin'].sum()
    
    if total_target_margin > 0:
        global_realization_pct = (total_actual_margin / total_target_margin) * 100
    elif total_target_margin == 0 and total_actual_margin >= 0:
        global_realization_pct = 100.0
    else:
        global_realization_pct = 0.0
    
    return {
        'total_deal_value': total_volume,
        'total_actual_revenue': total_actual_revenue,
        'total_target_revenue': total_target_revenue,
        'total_cost': total_cost,
        'total_actual_margin': total_actual_margin,
        'total_target_margin': total_target_margin,
        'global_realization_pct': global_realization_pct,
        'row_count': len(results_df),
    }


def aggregate_all_products(product_results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Aggregate metrics across all products.
    """
    all_results = []
    for material_code, results_df in product_results.items():
        if not results_df.empty:
            all_results.append(results_df)
    
    if not all_results:
        return aggregate_deal_metrics(pd.DataFrame())
    
    combined_df = pd.concat(all_results, ignore_index=True)
    return aggregate_deal_metrics(combined_df)


def validate_deal_inputs(deal_inputs_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate deal inputs and return list of any errors.
    """
    errors = []
    
    required_columns = [
        'tx_variant', 'region_classification', 'volume_eur',
        'atv', 'tx_count', 'target_variable_pct', 'target_fixed_eur',
        'proposed_variable_pct', 'proposed_fixed_eur'
    ]
    
    missing_cols = set(required_columns) - set(deal_inputs_df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors
    
    for idx, row in deal_inputs_df.iterrows():
        row_num = int(idx) + 1
        
        tx_variant = row.get('tx_variant', None)
        if pd.isna(tx_variant) or str(tx_variant).strip() == '':
            continue
        
        region = row.get('region_classification', None)
        if pd.isna(region) or str(region).strip() == '':
            continue
        
        volume = row.get('volume_eur', 0)
        if pd.isna(volume):
            volume = 0
        if volume < 0:
            errors.append(f"Row {row_num}: Volume cannot be negative")
        
        tx_count = row.get('tx_count', 0)
        if pd.isna(tx_count):
            tx_count = 0
        if tx_count < 0:
            errors.append(f"Row {row_num}: Transaction count cannot be negative")
        
        proposed_var = row.get('proposed_variable_pct', 0)
        if pd.isna(proposed_var):
            proposed_var = 0
        if proposed_var < 0:
            errors.append(f"Row {row_num}: Proposed variable fee cannot be negative")
        
        proposed_fixed = row.get('proposed_fixed_eur', 0)
        if pd.isna(proposed_fixed):
            proposed_fixed = 0
        if proposed_fixed < 0:
            errors.append(f"Row {row_num}: Proposed fixed fee cannot be negative")
    
    return len(errors) == 0, errors


def filter_valid_rows(deal_inputs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows with missing or invalid data before calculations.
    """
    if deal_inputs_df.empty:
        return deal_inputs_df
    
    valid_rows = []
    for idx, row in deal_inputs_df.iterrows():
        tx_variant = row.get('tx_variant', None)
        region = row.get('region_classification', None)
        volume = row.get('volume_eur', None)
        
        if pd.isna(tx_variant) or str(tx_variant).strip() == '' or str(tx_variant) == 'nan':
            continue
        if pd.isna(region) or str(region).strip() == '' or str(region) == 'nan':
            continue
        if pd.isna(volume) or volume <= 0:
            continue
        
        valid_rows.append(idx)
    
    return deal_inputs_df.loc[valid_rows]


def get_realization_status(realization_pct: float) -> str:
    """
    Determine the status based on realization percentage.
    """
    if realization_pct >= 100:
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


def update_tx_counts_for_product(deal_data: pd.DataFrame) -> pd.DataFrame:
    """
    Update transaction counts based on volume/ATV for each row.
    Handles NaN/blank values gracefully.
    """
    if deal_data.empty:
        return deal_data
    
    updated_data = deal_data.copy()
    
    for idx, row in updated_data.iterrows():
        volume = row.get('volume_eur', None)
        atv = row.get('atv', None)
        
        if pd.isna(volume) or volume == '' or volume is None:
            volume = 0.0
        else:
            try:
                volume = float(volume)
            except (ValueError, TypeError):
                volume = 0.0
        
        if pd.isna(atv) or atv == '' or atv is None:
            atv = 1.0
        else:
            try:
                atv = float(atv)
            except (ValueError, TypeError):
                atv = 1.0
        
        if atv <= 0:
            atv = 1.0
        
        expected_tx = calculate_tx_count_from_atv(volume, atv)
        updated_data.at[idx, 'tx_count'] = expected_tx
    
    return updated_data
