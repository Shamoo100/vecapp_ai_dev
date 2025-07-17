I need to analyze the current codebase structure to create a comprehensive folder reference that will help avoid duplicate migration paths and provide clear guidance for future file additions.
            - `/migrations/` folder is a duplicate of the active migration system.
            - New migration files should be added to `/app/database/migrations/`
            
toolName: view_folder
            
status: success
          
/Users/determinastechnologies/Documents/vecapp_ai/vecap-ai-refactor_base
          
# VecApp AI Codebase Folder Structure Reference

I've analyzed your codebase and created this comprehensive folder structure reference to help you understand the correct paths and avoid adding files to incorrect locations like the duplicate `/migrations/` folder.

## 🚨 **IMPORTANT: Avoid These Duplicate Paths**

**❌ INCORRECT (Legacy/Duplicate):**
- `/Users/determinastechnologies/Documents/vecapp_ai/vecap-ai-refactor_base/migrations/`

**✅ CORRECT (Active Migration System):**
- `/Users/determinastechnologies/Documents/vecapp_ai/vecap-ai-refactor_base/app/database/migrations/`

---

## 📁 **Complete Folder Structure Reference**

### **Root Level**
```
vecap-ai-refactor_base/
├── .dockerignore
├── .github/workflows/          # GitHub Actions CI/CD
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── Makefile
├── README.md
├── docker-compose.yaml
├── pyproject.toml
├── requirements.txt
├── check_and_drop_db.py
├── test_followup_api.py
└── test_response_integration.py
```

### **Main Application (`/app/`)**
```
app/
├── main.py                     # FastAPI application entry point
├── agents/                     # AI Agents (LangChain)
│   ├── base_agent.py
│   ├── data_collection_agent.py
│   ├── evaluation_agent.py
│   ├── feedback_loop_agent.py
│   ├── followup_note_agent.py
│   ├── followup_summary_agent.py
│   ├── specialist_agent.py
│   ├── test_agent.py
│   └── volunteer_coordination_agent.py
├── api/                        # FastAPI Routes & Schemas
│   ├── api.py                  # Main API router
│   ├── exceptions.py
│   ├── middleware.py
│   ├── routes/                 # API route handlers
│   │   ├── analytics.py
│   │   ├── auth_routes.py
│   │   ├── batch_tenants.py
│   │   ├── followup.py
│   │   ├── followup_notes.py
│   │   ├── followup_summary_report.py
│   │   ├── followup_task_processor.py
│   │   ├── tenants.py
│   │   ├── visitor.py
│   │   └── volunteer.py
│   ├── schemas/                # Pydantic models
│   │   ├── batch_tenant.py
│   │   ├── feedback.py
│   │   ├── metrics.py
│   │   ├── notes.py
│   │   ├── report.py
│   │   ├── schemas.py
│   │   ├── tenant.py
│   │   └── visitor.py
│   └── v1/                     # API versioning
│       └── feedback.py
├── config/
│   └── settings.py             # Application configuration
├── core/                       # Core utilities
│   ├── config.py
│   ├── messaging.py
│   ├── monitoring.py
│   └── notifications.py
├── data/                       # Data access layer
│   ├── ai/
│   │   └── vector_store.py
│   ├── cache/
│   │   └── repository_cache.py
│   ├── events/
│   │   ├── church_events_sample_data.json
│   │   ├── data_events.py
│   │   ├── task_sample_data.json
│   │   ├── team_sample_data.json
│   │   └── visitor_event_listener.py
│   ├── interfaces/
│   │   ├── report_repository.py
│   │   └── repository.py
│   ├── base_repository.py
│   ├── calendar_service.py
│   ├── connect_service.py
│   ├── data_fetcher.py
│   ├── event_driven_repository.py
│   ├── external_services_manager.py
│   ├── member_profile.sql
│   ├── member_service.py
│   ├── report_repository.py
│   ├── sqs_client.py
│   ├── storage.py
│   ├── unit_of_work.py
│   └── visitor_repository.py
└── ...
```

### **🗄️ Database Layer (`/app/database/`)**
```
database/
├── migrations/                 # ✅ CORRECT MIGRATION PATH
│   ├── migrate.py             # Migration management script
│   ├── public/                # Public schema migrations
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   └── alembic.ini
│   └── tenant/                # Tenant schema migrations
│       ├── alembic/
│       │   ├── env.py
│       │   ├── script.py.mako
│       │   └── versions/
│       └── alembic.ini
├── models/                    # SQLAlchemy models
│   ├── analytics.py
│   ├── base.py
│   ├── common.py
│   ├── decision_audit.py
│   ├── enums.py
│   ├── family.py
│   ├── feedback.py
│   ├── followup_task.py
│   ├── metrics.py
│   ├── notes.py
│   ├── person.py
│   ├── recommendation_log.py
│   ├── reports.py
│   ├── suppression_log.py
│   ├── tenant.py
│   ├── tenant_registry.py
│   └── visitor.py
└── repositories/              # Database repositories
    ├── apply_tenant_migrations.py
    ├── base.py
    ├── connection.py
    ├── create_tenant.py
    ├── followup_task_repository.py
    ├── migrate_to_tenant_schemas.py
    ├── schema_migration.py
    ├── tenant.py
    ├── tenant_context.py
    └── tenant_management.py
```

### **🔧 Other Important Directories**
```
feedback/
└── langsmith_integration.py    # LangSmith integration

llm/                           # LangChain components
├── chains.py
└── prompts.py

orchestration/
└── report_generator.py        # Report generation

repositories/                  # Additional repositories
└── feedback_repository.py

security/                      # Authentication & authorization
├── api_key.py
├── auth.py
├── tenant_context.py
├── token_service.py
└── token_validator.py

services/                      # Business logic services
├── analytics_service.py
├── batch_tenant_service.py
├── langchain_service.py
├── messaging_service.py
├── multi_tenant_service.py
├── report_service.py
└── tenant_service.py

tests/                         # Test files
├── test_batch_tenant_provisioning.py
├── test_data_collection_agent.py
├── test_db_connection.py
├── test_external_db_connections.py
├── test_feedback_system.py
├── test_generative_agent.py
├── test_multi_tenant_system.py
├── test_schema_sync.py
├── test_tenant_api.py
├── test_tenant_provisioning.py
└── test_trace.py

utils/
└── pdf_generator.py           # Utility functions
```

### **📚 Supporting Directories**
```
docs/                          # Documentation
├── BATCH_TENANT_PROVISIONING.md
├── DUAL_MIGRATION_SYSTEM.md
├── FEEDBACK_REQ_.md
├── FEEDBACK_SYSTEM.md
├── FOLLOWUP_NOTES_README.md
├── MEMBER_SERVICE_INTEGRATION.md
├── MIGRATION_CLEANUP_SUMMARY.md
├── MIGRATION_ENHANCMENT_PLAN.md
├── MULTI_TENANT_SETUP.md
├── README_BATCH_TENANT_SYSTEM.md
├── README_MULTI_TENANT.md
└── TENANT_MIGRATION_COMPLETENESS_ANALYSIS.md

examples/                      # Example scripts
├── batch_tenant_provisioning_example.py
├── feedback_example.py
└── test_tenant_provisioning.py

infra/                         # Infrastructure configs
├── k8s-dev/
├── k8s-local/
└── k8s-prod/

protos/                        # Protocol buffers
└── followup_service.proto

deployments/                   # Deployment configs
└── kubernetes/
    └── vecapp-ai-depl.yaml
```

---

## 📋 **File Placement Guidelines**

### **When adding new files, use these paths:**

| File Type | Correct Path | Example |
|-----------|--------------|----------|
| **Database Migrations** | `app/database/migrations/` | `app/database/migrations/tenant/alembic/versions/` |
| **SQLAlchemy Models** | `app/database/models/` | `app/database/models/new_model.py` |
| **API Routes** | `app/api/routes/` | `app/api/routes/new_endpoint.py` |
| **Pydantic Schemas** | `app/api/schemas/` | `app/api/schemas/new_schema.py` |
| **Business Services** | `app/services/` | `app/services/new_service.py` |
| **AI Agents** | `app/agents/` | `app/agents/new_agent.py` |
| **Database Repositories** | `app/database/repositories/` | `app/database/repositories/new_repo.py` |
| **Tests** | `app/tests/` | `app/tests/test_new_feature.py` |
| **Documentation** | `docs/` | `docs/NEW_FEATURE.md` |
| **Examples** | `examples/` | `examples/new_example.py` |

### **❌ Avoid These Legacy Paths:**
- `/migrations/` (root level - contains only legacy SQL)
- Any files outside the `/app/` directory for application code

---

## 🎯 **Key Takeaways**

1. **Always use** `app/database/migrations/` for new database migrations
2. **Never add** migration files to the root `/migrations/` folder
3. **Follow the established** folder structure within `/app/`
4. **Use the dual migration system** (public/tenant) for database changes
5. **Keep related files together** (models, repositories, services)

This structure follows FastAPI + LangChain best practices and maintains clear separation of concerns for your multi-tenant AI application.
        