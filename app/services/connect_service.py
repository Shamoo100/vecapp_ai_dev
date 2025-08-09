"""
Connect Service for cross-service integration with VecApp Connect Service.

This service provides business logic for connection data operations and 
orchestrates the connect repository for database access.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
from datetime import datetime, timedelta

from app.data.interfaces.connect_service_interface import IConnectService
from app.data.repositories.connect_service_repository import ConnectRepository

logger = logging.getLogger(__name__)


class ConnectService:
    """
    Service for managing connection data integration with external Connect Service.
    
    This service handles business logic for connection operations and provides
    a clean interface for AI agents and other services to access connection data.
    """
    
    def __init__(self, tenant_identifier: str, connect_repository: Optional[ConnectRepository] = None):
        """
        Initialize the connect service.
        
        Args:
            tenant_identifier: The tenant identifier for MongoDB database naming
            connect_repository: Optional repository injection for testing
        """
        self.tenant_identifier = tenant_identifier
        self._repository = connect_repository or ConnectRepository(tenant_identifier)
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        await self._repository.initialize()
        logger.info(f"Connect service initialized for tenant: {self.tenant_identifier}")
    
    async def close(self) -> None:
        """Close the service and its dependencies."""
        await self._repository.close()
        logger.info("Connect service closed")
    
    async def get_tenant_connection(self, tenant_identifier: str):
        """
        Get a database connection for a specific tenant.
        
        Args:
            tenant_identifier: The tenant identifier for MongoDB database naming
            
        Returns:
            AsyncIOMotorDatabase instance for the tenant
        """
        # TODO: actual implementation
        return await self._repository.get_tenant_connection(tenant_identifier)
    
    async def get_person_connections(self, person_id: UUID, tenant_identifier: str = None) -> Dict[str, Any]:
        """
        Get connections for a specific person with relationship insights.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            
        Returns:
            Dictionary containing connections and insights
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            connections = await self._repository.get_person_connections(person_id, tenant_id)
            
            # Add business logic insights
            insights = {
                'total_connections': len(connections),
                'active_connections': len([c for c in connections if c.get('status') == 'active']),
                'connection_types': self._analyze_connection_types(connections),
                'recent_connections': self._get_recent_connections(connections, days=30)
            }
            
            return {
                'connections': connections,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error getting person connections for {person_id} in tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_interaction_history(self, person_id: UUID, tenant_identifier: str = None, days_back: int = 90) -> Dict[str, Any]:
        """
        Get interaction history for a person with analytics.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            days_back: Number of days to look back for interactions
            
        Returns:
            Dictionary containing interactions and analytics
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            interactions = await self._repository.get_interaction_history(person_id, tenant_id, days_back)
            
            # Add interaction analytics
            analytics = {
                'total_interactions': len(interactions),
                'interactions_by_type': self._group_by_interaction_type(interactions),
                'interactions_by_week': self._group_by_week(interactions),
                'most_frequent_contacts': self._get_frequent_contacts(interactions),
                'interaction_trends': self._analyze_interaction_trends(interactions)
            }
            
            return {
                'interactions': interactions,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting interaction history for {person_id} in tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_public_groups(self, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get all public groups.
        
        Args:
            tenant_identifier: The tenant identifier (required for multi-tenant data isolation)
        
        Returns:
            List of public groups
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for multi-tenant data isolation")
                
            groups = await self._repository.get_public_groups(tenant_identifier)
            return groups
            
        except Exception as e:
            logger.error(f"Error getting public groups in tenant {tenant_identifier}: {str(e)}")
            raise

    async def get_all_teams(self, tenant_identifier: str) -> List[Dict[str, Any]]:
        """
        Get all teams (all teams are private in VecApp).
        
        Args:
            tenant_identifier: The tenant identifier (required for multi-tenant data isolation)
        
        Returns:
            List of all teams
        """
        try:
            if not tenant_identifier:
                raise ValueError("Tenant identifier is required for multi-tenant data isolation")
                
            teams = await self._repository.get_all_teams(tenant_identifier)
            return teams
            
        except Exception as e:
            logger.error(f"Error getting teams in tenant {tenant_identifier}: {str(e)}")
            raise
    
    async def get_group_connections(self, tenant_identifier: str = None, group_type: str = None) -> Dict[str, Any]:
        """
        Get group connections with connection analytics.
        
        Args:
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            group_type: Optional filter by group type
            
        Returns:
            Dictionary containing group connections and analytics
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            groups = await self._repository.get_group_connections(tenant_id, group_type)
            
            # Add connection analytics
            analytics = {
                'total_groups': len(groups),
                'groups_by_type': self._group_by_type(groups),
                'connection_strength': self._analyze_connection_strength(groups),
                'group_activity_levels': self._analyze_group_activity(groups)
            }
            
            return {
                'group_connections': groups,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting group connections in tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_person_groups(self, person_id: UUID, tenant_identifier: str = None) -> Dict[str, Any]:
        """
        Get groups that a person belongs to with membership insights.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            
        Returns:
            Dictionary containing group memberships and insights
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            memberships = await self._repository.get_person_groups(person_id, tenant_id)
            
            # Add membership insights
            insights = {
                'total_memberships': len(memberships),
                'active_memberships': len([m for m in memberships if m.get('status') == 'active']),
                'membership_roles': self._analyze_membership_roles(memberships),
                'group_types': self._analyze_group_types(memberships),
                'leadership_positions': self._count_leadership_positions(memberships)
            }
            
            return {
                'memberships': memberships,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error getting groups for person {person_id} in tenant {tenant_id}: {str(e)}")
            raise
    
    async def create_interaction(self, interaction_data: Dict[str, Any], tenant_identifier: str = None) -> Dict[str, Any]:
        """
        Create a new interaction record with validation and enhancement.
        
        Args:
            interaction_data: Dictionary containing interaction information
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            
        Returns:
            Created interaction document with metadata
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            
            # Add business logic validation
            if not interaction_data.get('initiator_id') or not interaction_data.get('recipient_id'):
                raise ValueError("Both initiator_id and recipient_id are required")
            
            # Enhance interaction data with metadata
            enhanced_data = {
                **interaction_data,
                'created_by_service': 'ai_service',
                'interaction_source': 'ai_agent',
                'created_at': datetime.utcnow()
            }
            
            created_interaction = await self._repository.create_interaction(enhanced_data, tenant_id)
            logger.info(f"Interaction created between {interaction_data['initiator_id']} and {interaction_data['recipient_id']} in tenant {tenant_id}")
            
            return created_interaction
            
        except Exception as e:
            logger.error(f"Error creating interaction in tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_connection_strength(self, person_id: UUID, connected_person_id: UUID, tenant_identifier: str = None) -> Optional[Dict[str, Any]]:
        """
        Get connection strength metrics between two people with analysis.
        
        Args:
            person_id: The first person's unique identifier
            connected_person_id: The second person's unique identifier
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            
        Returns:
            Connection strength data with analysis or None if no connection exists
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            connection = await self._repository.get_connection_strength(person_id, connected_person_id, tenant_id)
            
            if not connection:
                return None
            
            # Add strength analysis
            strength_analysis = {
                'connection_duration': self._calculate_connection_duration(connection),
                'interaction_frequency': connection.get('interaction_frequency', 0),
                'strength_score': self._calculate_strength_score(connection),
                'relationship_type': connection.get('relationship_type', 'Unknown')
            }
            
            return {
                'connection': connection,
                'strength_analysis': strength_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting connection strength in tenant {tenant_id}: {str(e)}")
            raise
    
    async def get_recent_interactions(self, person_id: UUID, tenant_identifier: str = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get recent interactions for a person with summary.
        
        Args:
            person_id: The person's unique identifier
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            limit: Maximum number of interactions to return
            
        Returns:
            Dictionary containing recent interactions and summary
        """
        # TODO: actual implementation
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            interactions = await self._repository.get_recent_interactions(person_id, tenant_id, limit)
            
            # Add interaction summary
            summary = {
                'total_recent': len(interactions),
                'last_interaction': interactions[0].get('interaction_date') if interactions else None,
                'interaction_types': self._group_by_interaction_type(interactions),
                'unique_contacts': len(set([
                    i.get('initiator_id') if i.get('recipient_id') == str(person_id) else i.get('recipient_id')
                    for i in interactions
                ]))
            }
            
            return {
                'recent_interactions': interactions,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error getting recent interactions for {person_id} in tenant {tenant_id}: {str(e)}")
            raise
    
    async def health_check(self, tenant_identifier: str = None) -> Dict[str, Any]:
        """
        Perform health check on the MongoDB connection for a specific tenant.
        
        Args:
            tenant_identifier: The tenant identifier (optional, uses instance tenant if not provided)
            
        Returns:
            Health status information
        """
        try:
            tenant_id = tenant_identifier or self.tenant_identifier
            return await self._repository.health_check(tenant_id)
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'connect_mongodb',
                'tenant_identifier': tenant_id,
                'error': str(e),
                'checked_at': datetime.utcnow()
            }
    
    # Helper methods for business logic analysis
    def _analyze_connection_types(self, connections: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze connection types distribution."""
        # TODO: actual implementation
        types = {}
        for connection in connections:
            conn_type = connection.get('connection_type', 'Unknown')
            types[conn_type] = types.get(conn_type, 0) + 1
        return types
    
    def _get_recent_connections(self, connections: List[Dict[str, Any]], days: int) -> List[Dict[str, Any]]:
        """Get connections made within the last N days."""
        # TODO: actual implementation
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            c for c in connections 
            if c.get('created_at') and c['created_at'] >= cutoff_date
        ]
    
    def _group_by_interaction_type(self, interactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group interactions by type."""
        # TODO: actual implementation
        types = {}
        for interaction in interactions:
            interaction_type = interaction.get('interaction_type', 'Unknown')
            types[interaction_type] = types.get(interaction_type, 0) + 1
        return types
    
    def _group_by_week(self, interactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group interactions by week."""
        # TODO: actual implementation
        weeks = {}
        for interaction in interactions:
            interaction_date = interaction.get('interaction_date')
            if interaction_date:
                week_start = interaction_date.date() - timedelta(days=interaction_date.weekday())
                week_key = week_start.strftime('%Y-W%U')
                weeks[week_key] = weeks.get(week_key, 0) + 1
        return weeks
    
    def _get_frequent_contacts(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get most frequent contacts from interactions."""
        # TODO: actual implementation
        contact_counts = {}
        for interaction in interactions:
            initiator = interaction.get('initiator_id')
            recipient = interaction.get('recipient_id')
            
            if initiator:
                contact_counts[initiator] = contact_counts.get(initiator, 0) + 1
            if recipient:
                contact_counts[recipient] = contact_counts.get(recipient, 0) + 1
        
        # Return top 5 contacts
        sorted_contacts = sorted(contact_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'person_id': pid, 'interaction_count': count} for pid, count in sorted_contacts[:5]]
    
    def _analyze_interaction_trends(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze interaction trends over time."""
        # TODO: actual implementation
        if not interactions:
            return {'trend': 'no_data'}
        
        # Simple trend analysis based on recent vs older interactions
        total = len(interactions)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_count = len([i for i in interactions if i.get('interaction_date', datetime.min) >= recent_cutoff])
        
        trend = 'increasing' if recent_count > total * 0.6 else 'decreasing' if recent_count < total * 0.3 else 'stable'
        
        return {
            'trend': trend,
            'recent_percentage': (recent_count / total) * 100 if total > 0 else 0,
            'total_interactions': total,
            'recent_interactions': recent_count
        }
    
    def _group_by_category(self, groups: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group by category."""
        # TODO: actual implementation
        categories = {}
        for group in groups:
            category = group.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _calculate_average_group_size(self, groups: List[Dict[str, Any]]) -> float:
        """Calculate average group size."""
        # TODO: actual implementation
        if not groups:
            return 0.0
        
        total_members = sum(group.get('member_count', 0) for group in groups)
        return total_members / len(groups)
    
    def _calculate_average_team_size(self, teams: List[Dict[str, Any]]) -> float:
        """Calculate average team size."""
        # TODO: actual implementation
        if not teams:
            return 0.0
        
        total_members = sum(team.get('member_count', 0) for team in teams)
        return total_members / len(teams)
    
    def _group_by_department(self, teams: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group teams by department."""
        # TODO: actual implementation
        departments = {}
        for team in teams:
            dept = team.get('department', 'Unknown')
            departments[dept] = departments.get(dept, 0) + 1
        return departments
    
    def _analyze_team_sizes(self, teams: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze team size distribution."""
        # TODO: actual implementation
        size_ranges = {'small': 0, 'medium': 0, 'large': 0}
        
        for team in teams:
            size = team.get('member_count', 0)
            if size <= 5:
                size_ranges['small'] += 1
            elif size <= 15:
                size_ranges['medium'] += 1
            else:
                size_ranges['large'] += 1
        
        return size_ranges
    
    def _group_by_type(self, groups: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group by type."""
        # TODO: actual implementation
        types = {}
        for group in groups:
            group_type = group.get('group_type', 'Unknown')
            types[group_type] = types.get(group_type, 0) + 1
        return types
    
    def _analyze_connection_strength(self, groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze connection strength across groups."""
        # TODO: actual implementation
        if not groups:
            return {'average_strength': 0, 'strong_connections': 0}
        
        strengths = [group.get('connection_strength', 0) for group in groups]
        avg_strength = sum(strengths) / len(strengths)
        strong_connections = len([s for s in strengths if s > 0.7])
        
        return {
            'average_strength': avg_strength,
            'strong_connections': strong_connections,
            'total_groups': len(groups)
        }
    
    def _analyze_group_activity(self, groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze group activity levels."""
        # TODO: actual implementation
        if not groups:
            return {'high_activity': 0, 'medium_activity': 0, 'low_activity': 0}
        
        activity_levels = {'high_activity': 0, 'medium_activity': 0, 'low_activity': 0}
        
        for group in groups:
            activity_score = group.get('activity_score', 0)
            if activity_score > 0.7:
                activity_levels['high_activity'] += 1
            elif activity_score > 0.3:
                activity_levels['medium_activity'] += 1
            else:
                activity_levels['low_activity'] += 1
        
        return activity_levels
    
    def _analyze_membership_roles(self, memberships: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze membership roles distribution."""
        # TODO: actual implementation
        roles = {}
        for membership in memberships:
            role = membership.get('role', 'Member')
            roles[role] = roles.get(role, 0) + 1
        return roles
    
    def _analyze_group_types(self, memberships: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze group types from memberships."""
        # TODO: actual implementation
        types = {}
        for membership in memberships:
            group_type = membership.get('group_type', 'Unknown')
            types[group_type] = types.get(group_type, 0) + 1
        return types
    
    def _count_leadership_positions(self, memberships: List[Dict[str, Any]]) -> int:
        """Count leadership positions."""
        # TODO: actual implementation
        leadership_roles = ['Leader', 'Admin', 'Moderator', 'Coordinator']
        return len([m for m in memberships if m.get('role') in leadership_roles])
    
    def _calculate_connection_duration(self, connection: Dict[str, Any]) -> int:
        """Calculate connection duration in days."""
        # TODO: actual implementation
        created_at = connection.get('created_at')
        if not created_at:
            return 0
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return (datetime.now() - created_at).days
    
    def _calculate_strength_score(self, connection: Dict[str, Any]) -> float:
        """Calculate connection strength score."""
        # TODO: actual implementation
        # Simple scoring based on interaction frequency and duration
        frequency = connection.get('interaction_frequency', 0)
        duration = self._calculate_connection_duration(connection)
        
        # Normalize and combine scores
        frequency_score = min(frequency / 10.0, 1.0)  # Cap at 10 interactions
        duration_score = min(duration / 365.0, 1.0)   # Cap at 1 year
        
        return (frequency_score + duration_score) / 2.0

    # Removed duplicate get_public_teams method - all teams are private in VecApp

    async def get_ministry_opportunities(self, tenant: str = None) -> List[Dict[str, Any]]:
        """
        Get all ministry opportunities with detailed information.
        
        Args:
            tenant: The tenant identifier (optional, uses instance tenant if not provided)
        
        Returns:
            List of ministry opportunities with enhanced data
        """
        # TODO: actual implementation
        try:
            # Get all teams and public groups to create ministry opportunities
            all_teams = await self.get_all_teams(tenant)
            public_groups = await self.get_public_groups(tenant)
            
            ministry_opportunities = []
            
            # Convert teams to ministry opportunities
            for team in all_teams:
                opportunity = {
                    'id': f"ministry_{team.get('id')}",
                    'title': f"Join {team.get('name')}",
                    'type': 'team',
                    'category': team.get('department', 'General Ministry'),
                    'description': team.get('description', ''),
                    'requirements': team.get('join_requirements', 'Contact team leader'),
                    'time_commitment': team.get('time_commitment', 'Flexible'),
                    'skills_needed': team.get('skill_requirements', []),
                    'contact_person': team.get('contact_person', 'Ministry Leader'),
                    'current_openings': team.get('current_openings', 1),
                    'urgency': 'medium',
                    'training_provided': True,
                    'background_check_required': team.get('name', '').lower().find('children') != -1,
                    'meeting_schedule': team.get('meeting_frequency', 'Weekly'),
                    'location': 'Church Campus',
                    'start_date': 'Contact for details',
                    'team_data': team
                }
                ministry_opportunities.append(opportunity)
            
            # Convert groups to ministry opportunities
            for group in public_groups:
                opportunity = {
                    'id': f"ministry_{group.get('id')}",
                    'title': f"Join {group.get('name')}",
                    'type': 'group',
                    'category': group.get('category', 'Fellowship'),
                    'description': group.get('description', ''),
                    'requirements': 'Open to all members',
                    'time_commitment': group.get('meeting_frequency', 'Weekly') + ' meetings',
                    'skills_needed': [],
                    'contact_person': group.get('leader_name', 'Group Leader'),
                    'current_openings': group.get('max_members', 20) - group.get('member_count', 0),
                    'urgency': 'low',
                    'training_provided': False,
                    'background_check_required': False,
                    'meeting_schedule': group.get('meeting_frequency', 'Weekly'),
                    'location': group.get('meeting_location', 'Church Campus'),
                    'start_date': 'Next meeting cycle',
                    'duration': 'Ongoing',
                    'benefits': [
                        'Build community',
                        'Grow spiritually',
                        'Form friendships',
                        'Learn together'
                    ]
                }
                ministry_opportunities.append(opportunity)
            
            # Add some general ministry opportunities
            general_opportunities = [
                {
                    'id': 'ministry_general_1',
                    'title': 'Community Outreach Volunteer',
                    'type': 'outreach',
                    'category': 'Community Service',
                    'description': 'Help with community outreach events and programs',
                    'requirements': 'Heart for serving others',
                    'time_commitment': '2-4 hours per month',
                    'skills_needed': ['Communication', 'Compassion'],
                    'contact_person': 'Outreach Coordinator',
                    'current_openings': 10,
                    'urgency': 'medium',
                    'training_provided': True,
                    'background_check_required': False,
                    'meeting_schedule': 'As needed',
                    'location': 'Various community locations',
                    'start_date': 'Immediate',
                    'duration': 'Flexible',
                    'benefits': [
                        'Serve the community',
                        'Make a real impact',
                        'Meet new people',
                        'Flexible schedule'
                    ]
                },
                {
                    'id': 'ministry_general_2',
                    'title': 'Event Setup Volunteer',
                    'type': 'support',
                    'category': 'Event Support',
                    'description': 'Help set up and tear down for church events',
                    'requirements': 'Ability to lift and move equipment',
                    'time_commitment': '2-3 hours per event',
                    'skills_needed': ['Physical ability', 'Teamwork'],
                    'contact_person': 'Events Coordinator',
                    'current_openings': 15,
                    'urgency': 'high',
                    'training_provided': True,
                    'background_check_required': False,
                    'meeting_schedule': 'Event-based',
                    'location': 'Church Campus',
                    'start_date': 'Immediate',
                    'duration': 'Per event',
                    'benefits': [
                        'Support church events',
                        'Work as a team',
                        'Flexible commitment',
                        'Behind-the-scenes impact'
                    ]
                },
                {
                    'id': 'ministry_general_3',
                    'title': 'Small Group Leader',
                    'type': 'leadership',
                    'category': 'Discipleship',
                    'description': 'Lead a small group for spiritual growth and community',
                    'requirements': 'Spiritual maturity and leadership experience',
                    'time_commitment': '3-4 hours per week',
                    'skills_needed': ['Leadership', 'Biblical knowledge', 'Facilitation'],
                    'contact_person': 'Small Groups Pastor',
                    'current_openings': 5,
                    'urgency': 'high',
                    'training_provided': True,
                    'background_check_required': True,
                    'meeting_schedule': 'Weekly',
                    'location': 'Homes or church',
                    'start_date': 'Next semester',
                    'duration': 'Semester-based',
                    'benefits': [
                        'Develop leadership skills',
                        'Impact lives',
                        'Grow spiritually',
                        'Build deep relationships'
                    ]
                }
            ]
            
            ministry_opportunities.extend(general_opportunities)
            
            # Sort by urgency and current openings
            urgency_order = {'high': 3, 'medium': 2, 'low': 1}
            ministry_opportunities.sort(
                key=lambda x: (urgency_order.get(x['urgency'], 1), -x.get('current_openings', 0)),
                reverse=True
            )
            
            return ministry_opportunities
            
        except Exception as e:
            logger.error(f"Error getting ministry opportunities: {str(e)}")
            # Return basic opportunities if there's an error
            return [
                {
                    'id': 'ministry_basic_1',
                    'title': 'General Volunteer',
                    'type': 'general',
                    'category': 'General Ministry',
                    'description': 'Help with various church activities and events',
                    'requirements': 'Willing heart to serve',
                    'time_commitment': 'Flexible',
                    'skills_needed': [],
                    'contact_person': 'Volunteer Coordinator',
                    'current_openings': 20,
                    'urgency': 'medium',
                    'training_provided': True,
                    'background_check_required': False,
                    'meeting_schedule': 'As needed',
                    'location': 'Church Campus',
                    'start_date': 'Immediate',
                    'duration': 'Flexible',
                    'benefits': [
                        'Serve others',
                        'Build community',
                        'Flexible schedule',
                        'Make a difference'
                    ]
                }
            ]


