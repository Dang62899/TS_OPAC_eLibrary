"""
Health check endpoints for system monitoring
Provides status of database, cache, and overall system health
"""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.core.cache import cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(views.APIView):
    """
    Health check endpoint for monitoring.
    Available at: GET /api/v1/health/
    """
    
    permission_classes = [AllowAny]  # Don't require auth for monitoring
    authentication_classes = []  # Disable authentication for this endpoint

    def get(self, request):
        """
        Get system health status.
        
        Returns:
            - status: "healthy" or "degraded"
            - timestamp: Current server time
            - database: "ok" or "error"
            - cache: "ok" or "error"
            - checks: Detailed health checks
        """
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check database
        db_status = self._check_database()
        health_data["checks"]["database"] = db_status
        
        if db_status["status"] != "ok":
            health_data["status"] = "degraded"
        
        # Check cache
        cache_status = self._check_cache()
        health_data["checks"]["cache"] = cache_status
        
        if cache_status["status"] != "ok":
            health_data["status"] = "degraded"
        
        # Determine response status code
        response_status = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=response_status)

    @staticmethod
    def _check_database():
        """Check database connectivity"""
        
        try:
            # Execute a simple query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {
                "status": "ok",
                "message": "Database connection successful"
            }
        
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "error",
                "message": "Database connection failed"
            }

    @staticmethod
    def _check_cache():
        """Check cache connectivity"""
        
        try:
            # Try to set and get a test value
            test_key = "health_check_test"
            test_value = "ok"
            
            cache.set(test_key, test_value, 10)
            cached_value = cache.get(test_key)
            
            if cached_value == test_value:
                return {
                    "status": "ok",
                    "message": "Cache connection successful"
                }
            else:
                return {
                    "status": "error",
                    "message": "Cache value mismatch"
                }
        
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                "status": "error",
                "message": "Cache connection failed"
            }


class DetailedHealthCheckView(views.APIView):
    """
    Detailed health check endpoint.
    Available at: GET /api/v1/health/detailed/
    Requires authentication for detailed system metrics.
    """
    
    permission_classes = [AllowAny]  # For this example, allowing all. Restrict in production.

    def get(self, request):
        """
        Get detailed system health including metrics.
        
        Returns:
            - system_health: Overall health
            - timestamp: Server time
            - uptime: Server uptime (if available)
            - checks: Detailed checks with timing
            - metrics: System metrics
        """
        
        health_data = {
            "system_health": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "metrics": {}
        }
        
        # Database check with timing
        db_check = self._check_database_detailed()
        health_data["checks"]["database"] = db_check
        
        if db_check["status"] != "ok":
            health_data["system_health"] = "degraded"
        
        # Cache check with timing
        cache_check = self._check_cache_detailed()
        health_data["checks"]["cache"] = cache_check
        
        if cache_check["status"] != "ok":
            health_data["system_health"] = "degraded"
        
        # System metrics
        health_data["metrics"] = self._get_system_metrics()
        
        response_status = status.HTTP_200_OK if health_data["system_health"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=response_status)

    @staticmethod
    def _check_database_detailed():
        """Detailed database check with query timing"""
        
        try:
            import time
            
            start = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            return {
                "status": "ok",
                "message": "Database connection successful",
                "response_time_ms": round(elapsed, 2)
            }
        
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "error",
                "message": "Database connection failed",
                "error": str(e)
            }

    @staticmethod
    def _check_cache_detailed():
        """Detailed cache check with timing"""
        
        try:
            import time
            
            test_key = "health_check_detailed"
            test_value = {"test": "data"}
            
            start = time.time()
            
            cache.set(test_key, test_value, 10)
            cached_value = cache.get(test_key)
            
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            if cached_value == test_value:
                return {
                    "status": "ok",
                    "message": "Cache connection successful",
                    "response_time_ms": round(elapsed, 2)
                }
            else:
                return {
                    "status": "error",
                    "message": "Cache value mismatch"
                }
        
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                "status": "error",
                "message": "Cache connection failed",
                "error": str(e)
            }

    @staticmethod
    def _get_system_metrics():
        """Get system metrics"""
        
        try:
            import psutil  # type: ignore[import] - package in requirements.txt
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
            }
        
        except (ImportError, Exception):
            # psutil not installed or error occurred
            return {
                "cpu_percent": "unavailable",
                "memory_percent": "unavailable",
                "disk_percent": "unavailable",
            }
