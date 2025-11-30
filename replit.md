# Commercial Pricing Guidance & Realization

## Overview
A production-grade Streamlit application for commercial pricing guidance and realization analysis. Built with a modular architecture following Adyen-style internal tooling patterns.

## Current State
- Fully functional application with all core and advanced features implemented
- **PostgreSQL database integration** for persistent pricing data storage
- **Global Deal Settings** with Merchant Name, Deal Date, ATV, Industry, and ECOM/POS split
- Per-product deal matrices with inline Region configuration
- **ECOM/POS channel-specific pricing** for Acquiring and Processing services
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

### Deal Settings (Sidebar)
- **Merchant Name**: Text input for deal identification
- **Deal Date**: Date picker for deal effective date
- **Global ATV**: Average Transaction Value applied to all products (Tx Count = Volume / ATV)
- **Industry**: Dropdown with 13 options (Retail, Delivery Services, etc.)
- **ECOM Split %**: Slider 0-100%, splits volume between ECOM and POS channels

### Data Schema (Merged Pricing with Channel-Specific Costs)
**Table A: Product Catalog (catalog_df)**
- material_code: AcquiringService, ProcessingService, RevenueProtectService
- tx_variant: visa, mc, amex, maestro, N/A
- pricing_model: Blended, FixedPerTx, VariableOnly

**Table B: Pricing Data (pricing_df) - Merged Costs + Targets + Channel Pricing**
- material_code, tx_variant, region_classification
- cost_variable, cost_fixed (base cost structure)
- target_variable, target_fixed (base target pricing)
- ecom_cost_variable, ecom_cost_fixed (ECOM channel costs - typically lower)
- pos_cost_variable, pos_cost_fixed (POS channel costs - typically higher)
- ecom_target_variable, ecom_target_fixed (ECOM targets)
- pos_target_variable, pos_target_fixed (POS targets)

### Deal Matrix Columns (Per Product)
- tx_variant: Transaction variant selection
- region_classification: Europe Domestic, NorthAmerica Domestic, Global
- volume_eur: Deal volume in EUR
- tx_count: Transaction count (auto-calculated from Volume/Global ATV, read-only)
- target_variable_pct, target_fixed_eur: Pre-populated target pricing
- proposed_variable_pct, proposed_fixed_eur: User's sale price

### Calculation Logic
For Acquiring/Processing services (with ECOM/POS split):
- ECOM Volume = Volume * (ECOM Split % / 100)
- POS Volume = Volume * ((100 - ECOM Split %) / 100)
- ECOM Cost = (ECOM Vol * ecom_cost_var) + (ECOM Tx * ecom_cost_fixed)
- POS Cost = (POS Vol * pos_cost_var) + (POS Tx * pos_cost_fixed)
- Total Cost = ECOM Cost + POS Cost

For all products:
- Actual Revenue = (Volume * proposed_var) + (Tx * proposed_fixed)
- Target Revenue = (Volume * target_var) + (Tx * target_fixed)
- **Actual Margin = Actual Revenue - Total Cost**
- **Target Margin = Target Revenue - Total Cost**
- **Realization % = (Actual Margin / Target Margin) * 100**

### Key Features
1. Per-product deal matrices (Acquiring, Processing, Revenue Protect)
2. **Global Deal Settings** with ATV, Industry, and ECOM/POS split
3. **Channel-specific pricing** (ECOM typically 10% lower costs, POS 15% higher)
4. Target prices pre-populated from pricing data (adjustable as sale price)
5. Auto-calculation of Tx Count from Volume/Global ATV (read-only field)
6. Margin-based realization calculation (Actual vs Target Margin)
7. Color-coded realization indicators (red if < 95%)
8. Gap analysis chart (Target Margin vs Actual Margin vs Cost)
9. ECOM/POS volume breakdown in detailed results
10. CSV file upload for custom pricing data
11. Data export functionality (detailed results and summary CSV)
12. Historical deal comparison with trend visualization
13. Drill-down analysis by product line and transaction variant
14. Deal scenario comparison (side-by-side what-if analysis)

### Industry Options
- Delivery Services
- Transportation & Mobility
- Internet, Media, Software & Apps
- Gambling
- Financial Services
- Public Services
- Consumer & Business Services
- Non-Profit Organizations
- Entertainment & Amusement
- Food & Beverage
- Hospitality & Travel
- Retail
- Other

## Recent Changes
- November 30, 2025: Added Deal Settings with Global ATV, Industry, and ECOM/POS split
- November 30, 2025: Implemented channel-specific pricing (ECOM/POS) for Acquiring and Processing
- November 30, 2025: Made tx_count read-only (auto-calculated from Volume/Global ATV)
- November 30, 2025: PostgreSQL database integration with thread-safe seeding
- November 30, 2025: Initial implementation of full MVP

## User Preferences
- ECOM/POS split affects actual pricing calculations (not just reporting)

## Running the Application
```bash
streamlit run app.py --server.port 5000
```
