# Tenant Migration Completeness Analysis

## Overview
This document analyzes the completeness of the tenant migration by comparing the current migration file with all available model definitions to identify missing tables.

## Current Tenant Migration Status

### Tables Created in Current Migration
**File**: `app/database/migrations/tenant/alembic/versions/20250102_000001_create_tenant_schema_tables.py`

The current migration creates only **3 tables**:
1. `tenant` - Basic tenant information
2. `person` - Person/member records
3. `visitor` - Visitor tracking

## Model Files Analysis

### Existing Model Files in `app/database/models/`
1. ✅ `tenant.py` - **COVERED** in migration
2. ✅ `person.py` - **COVERED** in migration  
3. ✅ `visitor.py` - **COVERED** in migration
4. ❌ `notes.py` - **MISSING** from migration
5. ❌ `reports.py` - **MISSING** from migration
6. ❌ `feedback.py` - **MISSING** from migration
7. ❌ `decision_audit.py` - **MISSING** from migration
8. ❌ `recommendation_log.py` - **MISSING** from migration
9. ❌ `suppression_log.py` - **MISSING** from migration
10. ⚠️ `analytics.py` - **EMPTY FILE**
11. ⚠️ `family.py` - **EMPTY FILE**
12. ⚠️ `metrics.py` - **EMPTY FILE**
13. ✅ `tenant_registry.py` - **PUBLIC SCHEMA** (correctly not in tenant migration)
14. ✅ `base.py` - **BASE CLASS** (not a table)
15. ✅ `common.py` - **MIXINS** (not tables)
16. ✅ `enums.py` - **ENUMS** (not tables)

## Missing Tables Analysis

### 1. Notes Table (`notes.py`)
- **Table Name**: `notes`
- **Schema**: `tenant`
- **Purpose**: Store notes and AI-generated content
- **Key Fields**: 
  - `person_id` (FK to person)
  - `title`, `notes_body`
  - `is_ai_generated`, `ai_generated_at`
  - `is_edited`, `is_archived`

### 2. Reports Table (`reports.py`)
- **Table Name**: `reports`
- **Schema**: `tenant`
- **Purpose**: Store generated reports (Snapshot, Journey, Weekly)
- **Key Fields**:
  - `tenant_id` (FK to tenant)
  - `report_type`, `date_range_start`, `date_range_end`
  - `content` (JSONB)
  - `generated_by`, `generated_at`

### 3. AI Feedback Analysis Table (`feedback.py`)
- **Table Name**: `ai_feedback_analysis`
- **Schema**: `tenant`
- **Purpose**: Store AI-generated feedback analysis
- **Key Fields**:
  - `person_id` (FK to person)
  - `feedback_category`, `tone`
  - `suggested_action`, `feedback_text`
  - `confidence_score`

### 4. AI Decision Audit Table (`decision_audit.py`)
- **Table Name**: `ai_decision_audit`
- **Schema**: `tenant`
- **Purpose**: Audit trail for AI decisions
- **Key Fields**:
  - `person_id` (FK to person)
  - `rule_id`, `rule_description`
  - `input_data`, `output_data` (JSON)
  - `triggered` (Boolean)

### 5. AI Recommendation Log Table (`recommendation_log.py`)
- **Table Name**: `ai_recommendation_log`
- **Schema**: `tenant`
- **Purpose**: Log AI recommendations
- **Key Fields**:
  - `person_id`, `fam_id`
  - `module_name`, `recommended_entity_type`
  - `recommendation_score`, `recommendation_tier`
  - `rationale`

### 6. AI Suppression Log Table (`suppression_log.py`)
- **Table Name**: `ai_suppression_log`
- **Schema**: `tenant`
- **Purpose**: Log suppressed AI actions
- **Key Fields**:
  - `person_id`
  - `reason`, `module_name`
  - `suppressed_entity_id`

## Issues Found

### 1. Import Errors in Model Files
- **`feedback.py`**: Missing `Column` import from SQLAlchemy
- **`suppression_log.py`**: Missing `Column`, `Text` imports from SQLAlchemy
- **`common.py`**: Missing import statement at the beginning

### 2. Foreign Key Reference Issues
- **`reports.py`**: References `tenant.tenants.id` but should be `tenant.tenant.id`
- Several models reference `tenant.person.id` which is correct

### 3. UUID vs Integer ID Inconsistency
- Some models use `UUID` primary keys while others use `Integer`
- Migration creates `Integer` IDs but some models expect `UUID`

## Recommendations

### 1. Create Additional Migration
Create a new migration file to add the missing tables:
```bash
# Generate new migration
python -c "from app.database.migrations.migrate import MigrationManager; mm = MigrationManager(); mm.init_tenant()"
```

### 2. Fix Model Import Issues
Update the model files to fix import statements:
- Add missing `Column`, `Text` imports
- Fix incomplete import statements

### 3. Standardize ID Types
Decide on consistent ID strategy:
- Either use `UUID` for all tenant tables
- Or use `Integer` for all tenant tables
- Update models and migrations accordingly

### 4. Fix Foreign Key References
Correct the foreign key references in `reports.py`:
```python
tenant_id = Column(Integer, ForeignKey('tenant.tenant.id'), nullable=False)
```

### 5. Complete Empty Model Files
Either:
- Implement the empty model files (`analytics.py`, `family.py`, `metrics.py`)
- Or remove them if not needed

## Migration Completeness Score

**Current Status**: 3/9 tables (33% complete)

**Missing**: 6 critical tables for AI functionality

**Priority**: HIGH - The missing tables are essential for:
- AI-generated content and feedback
- Audit trails and logging
- Report generation
- Recommendation systems

## Next Steps

1. **Immediate**: Fix import errors in model files
2. **High Priority**: Create migration for missing tables
3. **Medium Priority**: Standardize ID types across models
4. **Low Priority**: Complete or remove empty model files

## Impact Assessment

Without these missing tables:
- AI features will not work properly
- No audit trail for AI decisions
- Report generation will fail
- Recommendation system cannot store logs
- Notes and feedback features unavailable

The current migration is **incomplete** and requires immediate attention to support the full application functionality.