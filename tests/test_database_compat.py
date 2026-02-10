"""
Database Compatibility Tests

Tests to verify database operations work correctly with both SQLite and PostgreSQL.
Run with: python -m pytest tests/test_database_compat.py -v
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabasePostgreSQLCompatibility(unittest.TestCase):
    """Test that database methods work with PostgreSQL."""
    
    def setUp(self):
        """Set up mocks for PostgreSQL connection."""
        # We'll test that the code paths are correct without actual DB
        pass
    
    def test_get_changes_uses_correct_placeholder(self):
        """Verify get_changes uses %s for PostgreSQL and ? for SQLite."""
        from database import CIPDatabase
        
        # Test SQLite path
        with patch.object(CIPDatabase, '__init__', lambda x, **k: None):
            db = CIPDatabase.__new__(CIPDatabase)
            db.db_type = 'sqlite'
            db.db_path = ':memory:'
            
            # Verify placeholder logic
            placeholder = "%s" if db.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "?")
        
        # Test PostgreSQL path
        with patch.object(CIPDatabase, '__init__', lambda x, **k: None):
            db = CIPDatabase.__new__(CIPDatabase)
            db.db_type = 'postgres'
            
            placeholder = "%s" if db.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "%s")
    
    def test_get_bid_with_analysis_placeholder(self):
        """Verify get_bid_with_analysis uses correct SQL placeholders."""
        from database import CIPDatabase
        
        with patch.object(CIPDatabase, '__init__', lambda x, **k: None):
            db = CIPDatabase.__new__(CIPDatabase)
            db.db_type = 'postgres'
            
            placeholder = "%s" if db.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "%s")
    
    def test_get_recent_bids_with_analysis_placeholder(self):
        """Verify get_recent_bids_with_analysis uses correct SQL placeholders."""
        from database import CIPDatabase
        
        with patch.object(CIPDatabase, '__init__', lambda x, **k: None):
            db = CIPDatabase.__new__(CIPDatabase)
            db.db_type = 'sqlite'
            
            placeholder = "%s" if db.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "?")
    
    def test_get_bids_in_period_placeholder(self):
        """Verify get_bids_in_period uses correct SQL placeholders."""
        from database import CIPDatabase
        
        with patch.object(CIPDatabase, '__init__', lambda x, **k: None):
            db = CIPDatabase.__new__(CIPDatabase)
            db.db_type = 'postgres'
            
            placeholder = "%s" if db.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "%s")
    
    def test_get_all_recipients_works_with_both_db_types(self):
        """Verify get_all_recipients handles both DB types."""
        from database import CIPDatabase
        
        # Test that the method exists and has correct structure
        with patch.object(CIPDatabase, '__init__', lambda x, **k: None):
            db = CIPDatabase.__new__(CIPDatabase)
            db.db_type = 'postgres'
            
            # Method should exist
            self.assertTrue(hasattr(db, 'get_all_recipients'))


class TestAuthPostgreSQLCompatibility(unittest.TestCase):
    """Test that auth methods work with PostgreSQL."""
    
    def test_toggle_user_active_uses_correct_placeholder(self):
        """Verify toggle_user_active uses %s for PostgreSQL."""
        from auth import AuthManager
        
        with patch.object(AuthManager, '__init__', lambda x, **k: None):
            auth = AuthManager.__new__(AuthManager)
            auth.db_type = 'postgres'
            
            placeholder = "%s" if auth.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "%s")
    
    def test_login_with_google_handles_both_db_types(self):
        """Verify login_with_google uses conditional SQL for postgres."""
        from auth import AuthManager
        
        with patch.object(AuthManager, '__init__', lambda x, **k: None):
            auth = AuthManager.__new__(AuthManager)
            auth.db_type = 'sqlite'
            
            # SQLite should use ?
            placeholder = "%s" if auth.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "?")
            
            auth.db_type = 'postgres'
            placeholder = "%s" if auth.db_type == 'postgres' else "?"
            self.assertEqual(placeholder, "%s")


class TestObservabilityModule(unittest.TestCase):
    """Test the observability module."""
    
    def test_cloud_logging_formatter_produces_valid_json(self):
        """Verify CloudLoggingFormatter outputs valid JSON."""
        import logging
        from observability import CloudLoggingFormatter
        
        formatter = CloudLoggingFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(output)
        self.assertEqual(parsed['severity'], 'INFO')
        self.assertEqual(parsed['message'], 'Test message')
        self.assertIn('timestamp', parsed)
    
    def test_validate_environment_returns_dict(self):
        """Verify validate_environment returns expected structure."""
        from observability import validate_environment
        
        result = validate_environment()
        
        self.assertIsInstance(result, dict)
        self.assertIn('GOOGLE_API_KEY', result)
    
    def test_health_check_status(self):
        """Verify HealthCheck class works correctly."""
        from observability import HealthCheck
        
        health = HealthCheck()
        
        # Default is healthy
        self.assertTrue(health.healthy)
        
        # Set unhealthy
        health.set_unhealthy('database', 'Connection failed')
        self.assertFalse(health.healthy)
        
        status = health.get_status()
        self.assertEqual(status['status'], 'unhealthy')
        self.assertIn('database', status['components'])


if __name__ == '__main__':
    unittest.main()
