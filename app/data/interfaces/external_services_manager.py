from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from app.services.member_service import MemberService
from app.services.calendar_service import CalendarService
from app.services.connect_service import ConnectService
from app.services.external_auth_service import ExternalAuthService

logger = logging.getLogger(__name__)

class ExternalServicesManager:
    """
    Manager for all external database services with hybrid data syncing support.
    
    This class provides a centralized way to manage connections to all external 
    databases and orchestrates both provisioning-time sync and on-demand data 
    pulling operations. Handles different tenant identification patterns:
    - PostgreSQL services: use schema_name for multi-tenancy
    - MongoDB services: use tenant identifier for database naming
    """
    
    def __init__(self):
        """Initialize the services manager."""
        self.member_service: Optional[MemberService] = None
        self.calendar_service: Optional[CalendarService] = None
        self.connect_service: Optional[ConnectService] = None
        self.auth_service: Optional[ExternalAuthService] = None
        self._initialized = False
        self._schema_name: Optional[str] = None
        self._tenant_identifier: Optional[str] = None
    
    async def initialize(self, schema_name: Optional[str] = None, tenant_identifier: Optional[str] = None) -> None:
        """Initialize all external services with proper tenant handling.
        
        Args:
            schema_name: PostgreSQL schema name for Member, Calendar, and Auth services
            tenant_identifier: Tenant identifier for MongoDB Connect service
        """
        if self._initialized:
            return
            
        self._schema_name = schema_name
        self._tenant_identifier = tenant_identifier or schema_name  # Fallback to schema_name
        
        try:
            # Initialize Member Service (PostgreSQL - uses schema_name)
            self.member_service = MemberService(schema_name) if schema_name else MemberService()
            await self.member_service.initialize()
            
            # Initialize Calendar Service (PostgreSQL - uses schema_name)
            self.calendar_service = CalendarService()
            await self.calendar_service.initialize()
            
            # Initialize Connect Service (MongoDB - uses tenant_identifier)
            self.connect_service = ConnectService(self._tenant_identifier)
            await self.connect_service.initialize()
            
            # Initialize Auth Service (PostgreSQL - uses schema_name)
            self.auth_service = AuthService(schema_name) if schema_name else AuthService()
            await self.auth_service.initialize()
            
            self._initialized = True
            logger.info(f"All external services initialized successfully - Schema: {schema_name}, Tenant: {self._tenant_identifier}")
        except Exception as e:
            logger.error(f"Failed to initialize external services: {str(e)}")
            await self.close()
            raise
    
    async def close(self) -> None:
        """Close all external service connections."""
        if self.member_service:
            await self.member_service.close()
        
        if self.calendar_service:
            await self.calendar_service.close()
        
        if self.connect_service:
            await self.connect_service.close()
        
        if self.auth_service:
            await self.auth_service.close()
        
        self._initialized = False
        logger.info("All external services closed")
    
    @asynccontextmanager
    async def get_services(self, schema_name: Optional[str] = None, tenant_identifier: Optional[str] = None):
        """Context manager for getting all services with proper tenant handling."""
        if not self._initialized:
            await self.initialize(schema_name, tenant_identifier)
        
        try:
            yield {
                'member': self.member_service,
                'calendar': self.calendar_service,
                'connect': self.connect_service,
                'auth': self.auth_service,
                'tenant_info': {
                    'schema_name': self._schema_name,
                    'tenant_identifier': self._tenant_identifier
                }
            }
        finally:
            # Services remain open for reuse
            pass
    
    # ========================================
    # PROVISIONING-TIME SYNC METHODS
    # ========================================
    
    async def sync_provisioning_data(self, tenant_id: UUID, schema_name: str, tenant_identifier: str = None) -> Dict[str, Any]:
        """
        Orchestrate complete provisioning-time data sync for a new tenant.
        
        Args:
            tenant_id: The tenant's unique identifier
            schema_name: PostgreSQL schema name for PostgreSQL services
            tenant_identifier: Tenant identifier for MongoDB services (defaults to schema_name)
            
        Returns:
            Comprehensive sync operation summary
        """
        if not self._initialized:
            await self.initialize(schema_name, tenant_identifier or schema_name)
        
        sync_results = {
            'tenant_id': str(tenant_id),
            'schema_name': schema_name,
            'tenant_identifier': tenant_identifier or schema_name,
            'sync_type': 'provisioning',
            'started_at': datetime.utcnow(),
            'services': {},
            'overall_status': 'in_progress'
        }
        
        try:
            # Sync Auth Service data (PostgreSQL)
            auth_result = await self._sync_auth_data(tenant_id, schema_name)
            sync_results['services']['auth'] = auth_result
            
            # Sync Member Service data (PostgreSQL)
            member_result = await self._sync_member_data(tenant_id, schema_name)
            sync_results['services']['member'] = member_result
            
            # Note: Connect service is on-demand only, no provisioning sync needed
            
            # Determine overall status
            all_successful = all(
                result.get('status') == 'completed' 
                for result in sync_results['services'].values()
            )
            
            sync_results['overall_status'] = 'completed' if all_successful else 'partial'
            sync_results['completed_at'] = datetime.utcnow()
            
            logger.info(f"Provisioning sync completed for tenant {tenant_id}: {sync_results['overall_status']}")
            return sync_results
            
        except Exception as e:
            sync_results['overall_status'] = 'failed'
            sync_results['error'] = str(e)
            sync_results['completed_at'] = datetime.utcnow()
            logger.error(f"Provisioning sync failed for tenant {tenant_id}: {str(e)}")
            raise
    
    async def _sync_auth_data(self, tenant_id: UUID, schema_name: str) -> Dict[str, Any]:
        """Sync auth service data during provisioning (PostgreSQL)."""
        try:
            # Sync user authentication data, roles, permissions
            users = await self.auth_service.sync_user_data(tenant_id)
            roles = await self.auth_service.sync_role_data(tenant_id)
            permissions = await self.auth_service.sync_permission_data(tenant_id)
            
            return {
                'service': 'auth',
                'database_type': 'postgresql',
                'schema_name': schema_name,
                'status': 'completed',
                'data_synced': {
                    'users': len(users),
                    'roles': len(roles),
                    'permissions': len(permissions)
                },
                'synced_at': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Auth data sync failed: {str(e)}")
            return {
                'service': 'auth',
                'database_type': 'postgresql',
                'schema_name': schema_name,
                'status': 'failed',
                'error': str(e),
                'synced_at': datetime.utcnow()
            }
    
    async def _sync_member_data(self, tenant_id: UUID, schema_name: str) -> Dict[str, Any]:
        """Sync member service data during provisioning (PostgreSQL)."""
        try:
            # Sync person, family, user types, user status, tasks, notes
            persons = await self.member_service.sync_person_data(tenant_id)
            families = await self.member_service.sync_family_data(tenant_id)
            user_types = await self.member_service.sync_user_types(tenant_id)
            user_status = await self.member_service.sync_user_status_data(tenant_id)
            tasks = await self.member_service.sync_task_data(tenant_id)
            notes = await self.member_service.sync_notes_data(tenant_id)
            
            return {
                'service': 'member',
                'database_type': 'postgresql',
                'schema_name': schema_name,
                'status': 'completed',
                'data_synced': {
                    'persons': len(persons),
                    'families': len(families),
                    'user_types': len(user_types),
                    'user_status': len(user_status),
                    'tasks': len(tasks),
                    'notes': len(notes)
                },
                'synced_at': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Member data sync failed: {str(e)}")
            return {
                'service': 'member',
                'database_type': 'postgresql',
                'schema_name': schema_name,
                'status': 'failed',
                'error': str(e),
                'synced_at': datetime.utcnow()
            }
    
    # ========================================
    # ON-DEMAND DATA PULLING METHODS
    # ========================================
    
    async def pull_calendar_data(self, tenant_id: UUID, **kwargs) -> Dict[str, Any]:
        """
        Pull calendar data on-demand (PostgreSQL).
        
        Args:
            tenant_id: The tenant's unique identifier
            **kwargs: Additional parameters for calendar data pulling
            
        Returns:
            Calendar data and operation summary
        """
        if not self._initialized:
            raise RuntimeError("Services not initialized")
        
        try:
            # Pull upcoming events
            events = await self.calendar_service.get_upcoming_events(
                tenant_id, 
                days_ahead=kwargs.get('days_ahead', 30)
            )
            
            return {
                'service': 'calendar',
                'database_type': 'postgresql',
                'operation': 'on_demand_pull',
                'status': 'completed',
                'data': {
                    'events': events,
                    'count': len(events)
                },
                'pulled_at': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Calendar data pull failed: {str(e)}")
            return {
                'service': 'calendar',
                'database_type': 'postgresql',
                'operation': 'on_demand_pull',
                'status': 'failed',
                'error': str(e),
                'pulled_at': datetime.utcnow()
            }
    
    async def pull_connect_data(self, tenant_identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Pull connect service data on-demand (MongoDB).
        
        Args:
            tenant_identifier: The tenant identifier for MongoDB
            **kwargs: Additional parameters for connect data pulling
            
        Returns:
            Connect data and operation summary
        """
        if not self._initialized:
            raise RuntimeError("Services not initialized")
        
        try:
            person_id = kwargs.get('person_id')
            
            if person_id:
                # Pull specific person's connections
                connections = await self.connect_service.get_person_connections(person_id, tenant_identifier)
                interactions = await self.connect_service.get_interaction_history(person_id, tenant_identifier)
                groups = await self.connect_service.get_person_groups(person_id, tenant_identifier)
                
                return {
                    'service': 'connect',
                    'database_type': 'mongodb',
                    'tenant_identifier': tenant_identifier,
                    'operation': 'on_demand_pull',
                    'status': 'completed',
                    'data': {
                        'connections': connections,
                        'interactions': interactions,
                        'groups': groups,
                        'person_id': str(person_id)
                    },
                    'pulled_at': datetime.utcnow()
                }
            else:
                # Pull general group connections
                groups = await self.connect_service.get_group_connections(tenant_identifier)
                teams = await self.connect_service.get_all_teams(tenant_identifier)
                public_groups = await self.connect_service.get_public_groups(tenant_identifier)
                
                return {
                    'service': 'connect',
                    'database_type': 'mongodb',
                    'tenant_identifier': tenant_identifier,
                    'operation': 'on_demand_pull',
                    'status': 'completed',
                    'data': {
                        'groups': groups,
                        'teams': teams,
                        'public_groups': public_groups,
                        'total_count': len(groups) + len(teams) + len(public_groups)
                    },
                    'pulled_at': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Connect data pull failed: {str(e)}")
            return {
                'service': 'connect',
                'database_type': 'mongodb',
                'tenant_identifier': tenant_identifier,
                'operation': 'on_demand_pull',
                'status': 'failed',
                'error': str(e),
                'pulled_at': datetime.utcnow()
            }
    
    async def pull_member_updates(self, tenant_id: UUID, since: datetime = None) -> Dict[str, Any]:
        """
        Pull updated member service data on-demand (PostgreSQL).
        
        Args:
            tenant_id: The tenant's unique identifier
            since: Optional timestamp to pull updates since
            
        Returns:
            Updated member data and operation summary
        """
        if not self._initialized:
            raise RuntimeError("Services not initialized")
        
        try:
            if since:
                # Pull incremental updates
                updated_persons = await self.member_service.get_updated_person_data(since)
                updated_notes = await self.member_service.get_updated_notes(since)
                
                return {
                    'service': 'member',
                    'database_type': 'postgresql',
                    'operation': 'incremental_pull',
                    'status': 'completed',
                    'data': {
                        'updated_persons': updated_persons,
                        'updated_notes': updated_notes,
                        'since': since.isoformat()
                    },
                    'pulled_at': datetime.utcnow()
                }
            else:
                # Pull recent visitors
                recent_visitors = await self.member_service.get_recent_visitors()
                
                return {
                    'service': 'member',
                    'database_type': 'postgresql',
                    'operation': 'recent_data_pull',
                    'status': 'completed',
                    'data': {
                        'recent_visitors': recent_visitors,
                        'count': len(recent_visitors)
                    },
                    'pulled_at': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Member data pull failed: {str(e)}")
            return {
                'service': 'member',
                'database_type': 'postgresql',
                'operation': 'on_demand_pull',
                'status': 'failed',
                'error': str(e),
                'pulled_at': datetime.utcnow()
            }
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all external services.
        
        Returns:
            Health status of all services
        """
        health_status = {
            'overall_status': 'healthy',
            'checked_at': datetime.utcnow(),
            'tenant_info': {
                'schema_name': self._schema_name,
                'tenant_identifier': self._tenant_identifier
            },
            'services': {}
        }
        
        services = {
            'member': {'service': self.member_service, 'type': 'postgresql'},
            'calendar': {'service': self.calendar_service, 'type': 'postgresql'},
            'connect': {'service': self.connect_service, 'type': 'mongodb'},
            'auth': {'service': self.auth_service, 'type': 'postgresql'}
        }
        
        for service_name, service_info in services.items():
            try:
                service = service_info['service']
                if service and hasattr(service, 'health_check'):
                    health_result = await service.health_check()
                    health_status['services'][service_name] = {
                        'status': 'healthy',
                        'database_type': service_info['type'],
                        'details': health_result
                    }
                else:
                    health_status['services'][service_name] = {
                        'status': 'not_initialized',
                        'database_type': service_info['type']
                    }
            except Exception as e:
                health_status['services'][service_name] = {
                    'status': f'unhealthy: {str(e)}',
                    'database_type': service_info['type']
                }
                health_status['overall_status'] = 'degraded'
        
        return health_status

# Global instance
external_services = ExternalServicesManager()