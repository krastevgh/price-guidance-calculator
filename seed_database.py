"""
Database Seeding Script for Commercial Pricing Guidance & Realization.
Populates the database with initial materials, variants, and pricing data.
"""

from models import Material, TxVariant, PricingRef, get_session, init_db


def seed_database():
    """Seed the database with initial pricing data."""
    init_db()
    
    session = get_session()
    
    try:
        existing = session.query(Material).first()
        if existing:
            print("Database already seeded. Skipping.")
            return False
        
        materials_data = [
            {
                'material_code': 'AcquiringService',
                'description': 'Card Acquiring Service',
                'pricing_model': 'Blended',
                'default_atv': 100.0
            },
            {
                'material_code': 'ProcessingService',
                'description': 'Transaction Processing Service',
                'pricing_model': 'FixedPerTx',
                'default_atv': 100.0
            },
            {
                'material_code': 'RevenueProtectService',
                'description': 'Revenue Protection Service',
                'pricing_model': 'VariableOnly',
                'default_atv': 100.0
            },
        ]
        
        materials = {}
        for m_data in materials_data:
            material = Material(**m_data)
            session.add(material)
            session.flush()
            materials[m_data['material_code']] = material
        
        variants_data = [
            ('AcquiringService', 'visa', 'Visa', 100.0),
            ('AcquiringService', 'mc', 'Mastercard', 95.0),
            ('AcquiringService', 'amex', 'American Express', 150.0),
            ('AcquiringService', 'maestro', 'Maestro', 45.0),
            ('ProcessingService', 'visa', 'Visa', 100.0),
            ('ProcessingService', 'mc', 'Mastercard', 95.0),
            ('ProcessingService', 'amex', 'American Express', 150.0),
            ('ProcessingService', 'maestro', 'Maestro', 45.0),
            ('RevenueProtectService', 'N/A', 'Not Applicable', 100.0),
        ]
        
        variants = {}
        for material_code, variant_code, display_name, default_atv in variants_data:
            variant = TxVariant(
                material_id=materials[material_code].id,
                variant_code=variant_code,
                display_name=display_name,
                default_atv=default_atv
            )
            session.add(variant)
            session.flush()
            variants[(material_code, variant_code)] = variant
        
        regions = ['Europe Domestic', 'NorthAmerica Domestic', 'Global']
        
        cost_matrix = {
            'Europe Domestic': {'var_base': 0.0015, 'fixed_base': 0.015},
            'NorthAmerica Domestic': {'var_base': 0.0018, 'fixed_base': 0.018},
            'Global': {'var_base': 0.0025, 'fixed_base': 0.025},
        }
        
        target_matrix = {
            'Europe Domestic': {'var_base': 0.006, 'fixed_base': 0.05},
            'NorthAmerica Domestic': {'var_base': 0.0065, 'fixed_base': 0.055},
            'Global': {'var_base': 0.008, 'fixed_base': 0.07},
        }
        
        product_cost_multipliers = {
            'AcquiringService': {'var': 1.0, 'fixed': 1.0},
            'ProcessingService': {'var': 0.0, 'fixed': 0.8},
            'RevenueProtectService': {'var': 0.5, 'fixed': 0.0},
        }
        
        product_target_multipliers = {
            'AcquiringService': {'var': 1.0, 'fixed': 1.0},
            'ProcessingService': {'var': 0.0, 'fixed': 1.2},
            'RevenueProtectService': {'var': 0.3, 'fixed': 0.0},
        }
        
        variant_multipliers = {
            'visa': 1.0,
            'mc': 1.05,
            'amex': 1.5,
            'maestro': 0.85,
            'N/A': 1.0,
        }
        
        for (material_code, variant_code), variant in variants.items():
            material = materials[material_code]
            cost_mult = product_cost_multipliers[material_code]
            target_mult = product_target_multipliers[material_code]
            var_mult = variant_multipliers[variant_code]
            
            for region in regions:
                cost_base = cost_matrix[region]
                target_base = target_matrix[region]
                
                cost_variable = round(cost_base['var_base'] * cost_mult['var'] * var_mult, 6)
                cost_fixed = round(cost_base['fixed_base'] * cost_mult['fixed'] * var_mult, 4)
                target_variable = round(target_base['var_base'] * target_mult['var'] * var_mult, 6)
                target_fixed = round(target_base['fixed_base'] * target_mult['fixed'] * var_mult, 4)
                
                pricing = PricingRef(
                    material_id=material.id,
                    variant_id=variant.id,
                    region_classification=region,
                    cost_variable=cost_variable,
                    cost_fixed=cost_fixed,
                    target_variable=target_variable,
                    target_fixed=target_fixed
                )
                session.add(pricing)
        
        session.commit()
        print("Database seeded successfully!")
        print(f"  - {len(materials)} materials")
        print(f"  - {len(variants)} variants")
        print(f"  - {len(variants) * len(regions)} pricing entries")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
