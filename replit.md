# Commercial Pricing Guidance & Realization

## Overview
A production-grade Streamlit application for commercial pricing guidance and realization analysis. Built with a modular architecture following Adyen-style internal tooling patterns.

## Current State
- Fully functional MVP with all core features implemented
- Modular 4-file architecture (data.py, logic.py, components.py, app.py)
- Real-time deal matrix with auto-calculated transaction counts
- KPI dashboard with realization metrics
- Gap analysis visualization with Plotly charts

## Project Architecture

### File Structure
- `app.py` - Entry point with page config, session state management, and main layout
- `components.py` - UI rendering functions (KPI cards, data editor, charts)
- `logic.py` - Pure Python functions for calculations and business rules
- `data.py` - Data loading and mock data generation (Digital Twin schema)

### Data Schema (Digital Twin)
**Table A: Product Catalog (catalog_df)**
- material_code: AcquiringService, ProcessingService, RevenueProtectService
- tx_variant: visa, mc, amex, maestro, N/A
- pricing_model: Blended, FixedPerTx, VariableOnly

**Table B: Cost Base (costs_df)**
- material_code, tx_variant, region_classification
- cost_variable, cost_fixed_eur

**Table C: Commercial Guidance (guidance_df)**
- material_code, tx_variant, price_guidance_classification
- min_vol_eur, max_vol_eur, valid_from, valid_to
- advised_fee_variable, advised_fee_fixed_eur

### Key Features
1. Interactive deal matrix with st.data_editor
2. Auto-calculation of Tx Count from Volume/ATV
3. Date-filtered guidance lookup with volume tier matching
4. ProcessingService exception handling (fixed-only pricing)
5. Color-coded realization indicators (red if < 95%)
6. Gap analysis chart (Target vs Actual vs Cost)
7. CSV file upload for custom costs/guidance data

## Recent Changes
- November 30, 2025: Initial implementation of full MVP

## User Preferences
- None specified yet

## Running the Application
```bash
streamlit run app.py --server.port 5000
```
