"""
Database connection test script for external services.

This script tests connections to:
- Member Service (PostgreSQL)
- Calendar Service (PostgreSQL) 
- Connect Service (MongoDB)
"""

import asyncio
import asyncpg
import motor.motor_asyncio
import logging
from typing import Dict, Any
from app.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionTester:
    """
    Test database connections for all external services.
    """
    
    def __init__(self):
        """Initialize the connection tester with settings."""
        self.settings = get_settings()
        self.test_results = {}
    
    async def test_member_service_connection(self) -> Dict[str, Any]:
        """
        Test PostgreSQL connection for Member Service.
        
        Returns:
            Dict containing test results
        """
        service_name = "Member Service (PostgreSQL)"
        logger.info(f"Testing {service_name} connection...")
        
        try:
            # Get the member service database URL from environment
            member_db_url = getattr(self.settings, 'MEMBER_SERVICE_DATABASE_URL', None)
            
            if not member_db_url:
                return {
                    "service": service_name,
                    "status": "FAILED",
                    "error": "MEMBER_SERVICE_DATABASE_URL not found in settings",
                    "connection_time": None
                }
            
            # Test connection
            import time
            start_time = time.time()
            
            connection = await asyncpg.connect(member_db_url)
            
            # Test basic query
            result = await connection.fetchval("SELECT version();")
            connection_time = time.time() - start_time
            
            # Test schema access (assuming 'public' schema for testing)
            schemas = await connection.fetch(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');"
            )
            
            await connection.close()
            
            return {
                "service": service_name,
                "status": "SUCCESS",
                "connection_time": f"{connection_time:.3f}s",
                "database_version": result,
                "available_schemas": [row['schema_name'] for row in schemas],
                "url": member_db_url.split('@')[1] if '@' in member_db_url else "Hidden"
            }
            
        except Exception as e:
            logger.error(f"{service_name} connection failed: {str(e)}")
            return {
                "service": service_name,
                "status": "FAILED",
                "error": str(e),
                "connection_time": None
            }
    
    async def test_calendar_service_connection(self) -> Dict[str, Any]:
        """
        Test PostgreSQL connection for Calendar Service.
        
        Returns:
            Dict containing test results
        """
        service_name = "Calendar Service (PostgreSQL)"
        logger.info(f"Testing {service_name} connection...")
        
        try:
            # Get the calendar service database URL from environment
            calendar_db_url = getattr(self.settings, 'CALENDAR_SERVICE_DATABASE_URL', None)
            
            if not calendar_db_url:
                return {
                    "service": service_name,
                    "status": "FAILED",
                    "error": "CALENDAR_SERVICE_DATABASE_URL not found in settings",
                    "connection_time": None
                }
            
            # Test connection
            import time
            start_time = time.time()
            
            connection = await asyncpg.connect(calendar_db_url)
            
            # Test basic query
            result = await connection.fetchval("SELECT version();")
            connection_time = time.time() - start_time
            
            # Test schema access
            schemas = await connection.fetch(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');"
            )
            
            await connection.close()
            
            return {
                "service": service_name,
                "status": "SUCCESS",
                "connection_time": f"{connection_time:.3f}s",
                "database_version": result,
                "available_schemas": [row['schema_name'] for row in schemas],
                "url": calendar_db_url.split('@')[1] if '@' in calendar_db_url else "Hidden"
            }
            
        except Exception as e:
            logger.error(f"{service_name} connection failed: {str(e)}")
            return {
                "service": service_name,
                "status": "FAILED",
                "error": str(e),
                "connection_time": None
            }
    
    async def test_connect_service_connection(self) -> Dict[str, Any]:
        """
        Test MongoDB connection for Connect Service.
        
        Returns:
            Dict containing test results
        """
        service_name = "Connect Service (MongoDB)"
        logger.info(f"Testing {service_name} connection...")
        
        try:
            # Get the connect service MongoDB URL from environment
            mongo_url = getattr(self.settings, 'CONNECT_SERVICE_MONGODB_URL', None)
            
            if not mongo_url:
                return {
                    "service": service_name,
                    "status": "FAILED",
                    "error": "CONNECT_SERVICE_MONGODB_URL not found in settings",
                    "connection_time": None
                }
            
            # Test connection
            import time
            start_time = time.time()
            
            client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
            
            # Test connection with ping
            await client.admin.command('ping')
            connection_time = time.time() - start_time
            
            # Get server info
            server_info = await client.admin.command('buildInfo')
            
            # List databases
            databases = await client.list_database_names()
            
            client.close()
            
            return {
                "service": service_name,
                "status": "SUCCESS",
                "connection_time": f"{connection_time:.3f}s",
                "mongodb_version": server_info.get('version', 'Unknown'),
                "available_databases": databases,
                "url": "MongoDB Atlas (Hidden credentials)"
            }
            
        except Exception as e:
            logger.error(f"{service_name} connection failed: {str(e)}")
            return {
                "service": service_name,
                "status": "FAILED",
                "error": str(e),
                "connection_time": None
            }
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """
        Test all database connections concurrently.
        
        Returns:
            Dict containing all test results
        """
        logger.info("Starting database connection tests...")
        
        # Run all tests concurrently
        tasks = [
            self.test_member_service_connection(),
            self.test_calendar_service_connection(),
            self.test_connect_service_connection()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        test_summary = {
            "total_services": len(tasks),
            "successful_connections": 0,
            "failed_connections": 0,
            "results": []
        }
        
        for result in results:
            if isinstance(result, Exception):
                test_summary["results"].append({
                    "service": "Unknown",
                    "status": "FAILED",
                    "error": str(result),
                    "connection_time": None
                })
                test_summary["failed_connections"] += 1
            else:
                test_summary["results"].append(result)
                if result["status"] == "SUCCESS":
                    test_summary["successful_connections"] += 1
                else:
                    test_summary["failed_connections"] += 1
        
        return test_summary
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """
        Print formatted test results.
        
        Args:
            results: Test results dictionary
        """
        print("\n" + "="*60)
        print("DATABASE CONNECTION TEST RESULTS")
        print("="*60)
        
        print(f"\nSummary:")
        print(f"  Total Services: {results['total_services']}")
        print(f"  Successful: {results['successful_connections']}")
        print(f"  Failed: {results['failed_connections']}")
        
        print(f"\nDetailed Results:")
        print("-" * 60)
        
        for result in results['results']:
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"\n{status_icon} {result['service']}")
            print(f"   Status: {result['status']}")
            
            if result['status'] == 'SUCCESS':
                print(f"   Connection Time: {result['connection_time']}")
                if 'database_version' in result:
                    print(f"   Database Version: {result['database_version']}")
                if 'mongodb_version' in result:
                    print(f"   MongoDB Version: {result['mongodb_version']}")
                if 'available_schemas' in result:
                    print(f"   Available Schemas: {', '.join(result['available_schemas'])}")
                if 'available_databases' in result:
                    print(f"   Available Databases: {', '.join(result['available_databases'])}")
                print(f"   URL: {result['url']}")
            else:
                print(f"   Error: {result['error']}")
        
        print("\n" + "="*60)


async def main():
    """
    Main function to run database connection tests.
    """
    tester = DatabaseConnectionTester()
    results = await tester.test_all_connections()
    tester.print_results(results)
    
    # Return exit code based on results
    if results['failed_connections'] > 0:
        print(f"\n⚠️  {results['failed_connections']} connection(s) failed!")
        return 1
    else:
        print(f"\n🎉 All {results['successful_connections']} connections successful!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)