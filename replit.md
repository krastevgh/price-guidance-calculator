# Commercial Pricing Guidance & Realization

## Overview
A production-grade Streamlit application for commercial pricing guidance and realization analysis. Built with a modular architecture following Adyen-style internal tooling patterns.

## Current State
- Fully functional application with all core and advanced features implemented
- **PostgreSQL database integration** for persistent pricing data storage
- Per-product deal matrices with inline Region and ATV configuration
- Margin-based realization calculation (Actual Margin vs Target Margin)
- KPI dashboard with realization metrics
- Gap analysis visualization with Plotly charts
- Data export, historical comparison, drill-down analysis, and scenario comparison

## Project Architecture

### File Structure
- `app.py` - Entry point with page config, session state management, and main layout
- `components.py` - UI rendering functions (KPI cards, data editor, charts, export, analysis)
- `logic.py` - Pure Python functions for calculations and business rules
- `data.py` - Data loading from database with fallback to mock data
- `models.py` - SQLAlchemy ORM models for database tables
- `repository.py` - Database access layer with caching
- `seed_database.py` - Script to populate database with initial pricing data

### Data Schema (Merged Pricing)
**Table A: Product Catalog (catalog_df)**
- material_code: AcquiringService, ProcessingService, RevenueProtectService
- tx_variant: visa, mc, amex, maestro, N/A
- pricing_model: Blended, FixedPerTx, VariableOnly
- default_atv: Default average transaction value

**Table B: Pricing Data (pricing_df) - Merged Costs + Targets**
- material_code, tx_variant, region_classification
- cost_variable, cost_fixed (cost structure)
- target_variable, target_fixed (target pricing)

### Deal Matrix Columns (Per Product)
- tx_variant: Transaction variant selection
- region_classification: Europe Domestic, NorthAmerica Domestic, Global
- volume_eur: Deal volume in EUR
- atv: Average Transaction Value (per-row)
- tx_count: Transaction count (auto-calculated from Volume/ATV)
- target_variable_pct, target_fixed_eur: Pre-populated target pricing
- proposed_variable_pct, proposed_fixed_eur: User's sale price

### Calculation Logic
- Actual Revenue = (Volume * proposed_var) + (Tx * proposed_fixed)
- Target Revenue = (Volume * target_var) + (Tx * target_fixed)
- Cost = (Volume * cost_var) + (Tx * cost_fixed)
- **Actual Margin = Actual Revenue - Cost**
- **Target Margin = Target Revenue - Cost**
- **Realization % = (Actual Margin / Target Margin) * 100**

### Key Features
1. Per-product deal matrices (Acquiring, Processing, Revenue Protect)
2. Per-row Region classification and ATV configuration
3. Target prices pre-populated from pricing data (adjustable as sale price)
4. Auto-calculation of Tx Count from Volume/ATV
5. ProcessingService exception handling (fixed-only pricing)
6. Margin-based realization calculation (Actual vs Target Margin)
7. Color-coded realization indicators (red if < 95%)
8. Gap analysis chart (Target Margin vs Actual Margin vs Cost)
9. CSV file upload for custom pricing data
10. Data export functionality (detailed results and summary CSV)
11. Historical deal comparison with trend visualization
12. Drill-down analysis by product line and transaction variant
13. Deal scenario comparison (side-by-side what-if analysis)

## Recent Changes
- November 30, 2025: Restructured to per-product deal matrices with inline Region/ATV, merged pricing schema, margin-based realization
- November 30, 2025: Added data export, historical comparison, drill-down analysis, scenario comparison
- November 30, 2025: Initial implementation of full MVP

## User Preferences
- None specified yet

## Running the Application
```bash
streamlit run app.py --server.port 5000
```
