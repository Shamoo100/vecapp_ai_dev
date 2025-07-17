# 📁 VecApp AI Codebase - Complete Folder Structure

Here's the comprehensive folder structure for your **VecApp AI FastAPI + LangChain** codebase:

```
vecap-ai-refactor_base/
├── 📄 Configuration & Setup
│   ├── .dockerignore
│   ├── .gitignore
│   ├── .pre-commit-config.yaml
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── Makefile
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── README.md
│
├── 🔄 CI/CD & GitHub Actions
│   └── .github/
│       └── workflows/
│           ├── 01-ai-build-dev.yml
│           ├── 01-ai-deploy-dev.yml
│           ├── 02-ai-build-prod.yml
│           └── 02-ai-deploy-prod.yml
│
├── 🚀 Main Application
│   └── app/
│       ├── __init__.py
│       ├── main.py                          # FastAPI application entry point
│       │
│       ├── 🤖 AI Agents & LLM
│       │   ├── agents/
│       │   │   ├── __init__.py
│       │   │   ├── base_agent.py            # Base agent class
│       │   │   ├── data_collection_agent.py # Data collection automation
│       │   │   ├── followup_note_agent.py   # Follow-up note generation
│       │   │   ├── followup_summary_agent.py# Summary generation
│       │   │   └── specialist_agent.py      # Specialized AI tasks
│       │   │
│       │   └── llm/
│       │       ├── __init__.py
│       │       ├── chains.py                # LangChain chains
│       │       └── prompts.py               # LLM prompt templates
│       │
│       ├── 🌐 API Layer
│       │   └── api/
│       │       ├── api.py                   # Main API router
│       │       ├── exceptions.py           # Custom exception handlers
│       │       ├── middleware.py           # Custom middleware
│       │       │
│       │       ├── schemas/                # Pydantic models
│       │       │   ├── __init__.py
│       │       │   ├── ai_models.py        # AI-related schemas
│       │       │   ├── feedback.py         # Feedback schemas
│       │       │   ├── notes.py            # Notes schemas
│       │       │   ├── report.py           # Report schemas
│       │       │   ├── task.py             # Task schemas
│       │       │   └── tenant.py           # Tenant schemas
│       │       │
│       │       ├── v1/                     # API Version 1
│       │       │   ├── __init__.py
│       │       │   └── routes/
│       │       │       ├── __init__.py
│       │       │       ├── auth_routes.py  # Authentication endpoints
│       │       │       ├── feedback.py     # Feedback endpoints
│       │       │       └── followup_notes.py # Follow-up notes endpoints
│       │       │
│       │       └── v2/                     # API Version 2
│       │           └── __init__.py
│       │
│       ├── ⚙️ Configuration
│       │   └── config/
│       │       ├── __init__.py
│       │       ├── messaging_setup.py      # Message queue configuration
│       │       ├── monitoring.py           # Monitoring setup
│       │       ├── notifications.py        # Notification configuration
│       │       └── settings.py             # Application settings
│       │
│       ├── 💾 Data Layer
│       │   └── data/
│       │       ├── __init__.py
│       │       ├── unit_of_work.py         # Unit of Work pattern
│       │       │
│       │       ├── cache/                  # Caching layer
│       │       │   └── repository_cache.py
│       │       │
│       │       └── interfaces/             # Repository interfaces
│       │           ├── ai_task_repository.py
│       │           ├── event_driven_repository.py
│       │           ├── external_services_manager.py
│       │           ├── feedback_repository.py
│       │           ├── report_repository.py
│       │           ├── repository.py
│       │           └── visitor_repository.py
│       │
│       ├── 🗄️ Database Layer
│       │   └── database/
│       │       ├── __init__.py
│       │       │
│       │       ├── models/                 # SQLAlchemy models
│       │       │   ├── __init__.py
│       │       │   ├── base.py             # Base model classes
│       │       │   ├── common.py           # Common model utilities
│       │       │   ├── enums.py            # Database enums
│       │       │   │
│       │       │   ├── public/             # Public schema models
│       │       │   │   ├── __init__.py
│       │       │   │   └── tenant_registry.py
│       │       │   │
│       │       │   └── tenant/             # Tenant-specific models
│       │       │       ├── __init__.py
│       │       │       ├── ai_fam.py       # AI family models
│       │       │       ├── ai_notes.py     # AI notes models
│       │       │       ├── ai_person.py    # AI person models
│       │       │       ├── ai_task.py      # AI task models
│       │       │       ├── decision_audit.py
│       │       │       ├── feedback.py
│       │       │       ├── recommendation_log.py
│       │       │       ├── reports.py
│       │       │       ├── suppression_log.py
│       │       │       └── tenant.py
│       │       │
│       │       ├── migrations/             # Database migrations
│       │       │   ├── __init__.py
│       │       │   ├── migrate.py          # Migration utilities
│       │       │   │
│       │       │   ├── public/             # Public schema migrations
│       │       │   │   ├── __init__.py
│       │       │   │   ├── alembic.ini
│       │       │   │   └── alembic/
│       │       │   │       ├── __init__.py
│       │       │   │       ├── env.py
│       │       │   │       ├── script.py.mako
│       │       │   │       └── versions/
│       │       │   │
│       │       │   └── tenant/             # Tenant schema migrations
│       │       │       ├── __init__.py
│       │       │       ├── alembic.ini
│       │       │       └── alembic/
│       │       │           ├── __init__.py
│       │       │           ├── env.py
│       │       │           ├── script.py.mako
│       │       │           └── versions/
│       │       │
│       │       └── repositories/           # Data access layer
│       │           ├── apply_tenant_migrations.py
│       │           ├── base_repository.py  # Base repository class
│       │           ├── connection.py       # Database connections
│       │           ├── migrate_to_tenant_schemas.py
│       │           ├── schema_migration.py
│       │           ├── tenant.py           # Tenant repository
│       │           ├── tenant_context.py   # Tenant context management
│       │           └── tenant_management.py
│       │
│       ├── 📡 Events & Messaging
│       │   └── events/
│       │       └── visitor_event_listener.py
│       │
│       ├── 📊 Feedback & Monitoring
│       │   └── feedback/
│       │       └── langsmith_integration.py
│       │
│       ├── 🏗️ Infrastructure
│       │   └── infastructure/              # Note: typo in original
│       │       ├── ai/                     # AI infrastructure
│       │       │   ├── __init__.py
│       │       │   └── vector_store.py
│       │       │
│       │       ├── aws/                    # AWS services
│       │       │   ├── __init__.py
│       │       │   ├── s3_storage.py
│       │       │   └── sqs_client.py
│       │       │
│       │       └── external/               # External integrations
│       │           ├── __init__.py
│       │           └── data_fetcher.py
│       │
│       ├── 🎯 Orchestration
│       │   └── orchestration/
│       │       └── report_generator.py
│       │
│       ├── 🔐 Security
│       │   └── security/
│       │       ├── __init__.py
│       │       ├── api_key.py              # API key management
│       │       ├── auth.py                 # Authentication
│       │       ├── tenant_context.py       # Multi-tenant context
│       │       ├── token_service.py        # Token management
│       │       └── token_validator.py      # Token validation
│       │
│       ├── 🔧 Business Services
│       │   └── services/
│       │       ├── __init__.py
│       │       ├── analytics_service.py    # Analytics functionality
│       │       ├── batch_tenant_service.py # Batch tenant operations
│       │       ├── calendar_service.py     # Calendar integration
│       │       ├── connect_service.py      # Connection services
│       │       ├── followup_service.py     # Follow-up management
│       │       ├── langchain_service.py    # LangChain integration
│       │       ├── member_service.py       # Member management
│       │       ├── messaging_service.py    # Messaging functionality
│       │       ├── multi_tenant_service.py # Multi-tenant operations
│       │       ├── report_service.py       # Report generation
│       │       └── tenant_service.py       # Tenant management
│       │
│       ├── 🧪 Testing
│       │   └── tests/
│       │       ├── test_batch_tenant_provisioning.py
│       │       ├── test_data_collection_agent.py
│       │       ├── test_db_connection.py
│       │       ├── test_external_db_connections.py
│       │       ├── test_feedback_system.py
│       │       ├── test_followup_api.py
│       │       ├── test_generative_agent.py
│       │       ├── test_multi_tenant_system.py
│       │       ├── test_response_integration.py
│       │       ├── test_schema_sync.py
│       │       ├── test_tenant_api.py
│       │       ├── test_tenant_provisioning.py
│       │       └── test_trace.py
│       │
│       └── 🛠️ Utilities
│           └── utils/
│               ├── __init__.py
│               └── pdf_generator.py
│
├── 🚢 Deployment & Infrastructure
│   ├── deployments/
│   │   └── kubernetes/
│   │       └── vecapp-ai-depl.yaml
│   │
│   └── infra/
│       ├── k8s-dev/
│       │   └── k8s-apps/
│       │       └── vecap-ai-depl.yml
│       │
│       ├── k8s-local/
│       │   ├── analytics-deployment.yaml
│       │   └── deployment.yaml
│       │
│       └── k8s-prod/
│           └── k8s-apps/
│               └── vecap-ai-depl.yml
│
├── 📚 Documentation
│   └── docs/
│       ├── BATCH_TENANT_PROVISIONING.md
│       ├── DUAL_MIGRATION_SYSTEM.md
│       ├── FEEDBACK_REQ_.md
│       ├── FEEDBACK_SYSTEM.md
│       ├── FOLDER_STRUCTURE_GUIDE.md
│       ├── FOLLOWUP_NOTES_README.md
│       ├── MEMBER_SERVICE_INTEGRATION.md
│       ├── MIGRATION_CLEANUP_SUMMARY.md
│       ├── MIGRATION_ENHANCMENT_PLAN.md
│       ├── MULTI_TENANT_SETUP.md
│       ├── README_BATCH_TENANT_SYSTEM.md
│       ├── README_MULTI_TENANT.md
│       ├── TENANT_MIGRATION_COMPLETENESS_ANALYSIS.md
│       │
│       └── sample_data/
│           ├── church_events_sample_data.json
│           ├── member_profile.sql
│           ├── task_sample_data.json
│           └── team_sample_data.json
│
├── 💡 Examples & Prototypes
│   └── examples/
│       ├── batch_tenant_provisioning_example.py
│       ├── check_and_drop_db.py
│       ├── feedback_example.py
│       └── test_tenant_provisioning.py
│
└── 🔌 Protocol Buffers
    └── protos/
        └── followup_service.proto
```

## 🏗️ Architecture Overview

This codebase follows a **clean architecture** pattern with clear separation of concerns:

### **🎯 Key Architectural Patterns:**
- **Multi-tenant SaaS** with schema-based tenant isolation
- **Repository Pattern** for data access abstraction
- **Unit of Work** for transaction management
- **CQRS-like** separation with dedicated read/write operations
- **Event-driven** architecture for loose coupling
- **Microservices-ready** with clear service boundaries

### **🔧 Technology Stack:**
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration and AI agents
- **PostgreSQL** - Multi-tenant database with schema isolation
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations (dual: public + tenant)
- **AsyncPG** - High-performance async PostgreSQL driver
- **Kubernetes** - Container orchestration
- **AWS** - Cloud infrastructure (S3, SQS)

### **🚀 Notable Features:**
- **Dual Migration System** - Separate migrations for public and tenant schemas
- **AI Agent Framework** - Modular AI agents for different tasks
- **Comprehensive Testing** - Full test coverage across all layers
- **Multi-environment Support** - Dev, staging, and production configurations
- **Advanced Security** - JWT, API keys, and tenant isolation

This structure supports scalable, maintainable, and secure multi-tenant AI applications with clear boundaries between different architectural layers.
        