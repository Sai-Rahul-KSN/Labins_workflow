"""
Database module for BLMID Validator.
Manages PostgreSQL connections and queries.
"""

import logging
from typing import Dict, List, Optional
import psycopg2
from psycopg2 import pool, Error
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """PostgreSQL database connector for BLMID verification."""

    def __init__(
        self,
        connection_uri: str,
        table_name: str = "blmid_reference",
        blmid_column: str = "blmid",
        latitude_column: str = "latitude",
        longitude_column: str = "longitude",
    ):
        """
        Initialize database connector.

        Args:
            connection_uri: PostgreSQL connection URI (postgresql://user:password@host:port/database)
            table_name: Table name for BLMID reference
            blmid_column: BLMID column name
            latitude_column: Latitude column name
            longitude_column: Longitude column name
        """
        self.connection_uri = connection_uri
        self.table_name = table_name
        self.blmid_column = blmid_column
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
        self.connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._test_connection()

    def _test_connection(self) -> None:
        """Test database connection on initialization."""
        try:
            conn = self._get_connection()
            conn.close()
            logger.info("Database connection successful")
        except Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _get_connection(self):
        """Get a database connection."""
        try:
            conn = psycopg2.connect(self.connection_uri)
            return conn
        except Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def find_by_coordinates(
        self, latitude: float, longitude: float, tolerance: float = 0.0001
    ) -> Optional[Dict]:
        """
        Query database for BLMID matching coordinates.

        Args:
            latitude: Target latitude
            longitude: Target longitude
            tolerance: Tolerance in degrees

        Returns:
            Dict with BLMID and coordinates or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = f"""
                SELECT {self.blmid_column}, {self.latitude_column}, {self.longitude_column}
                FROM {self.table_name}
                WHERE ABS({self.latitude_column} - %s) <= %s
                  AND ABS({self.longitude_column} - %s) <= %s
                LIMIT 1;
            """

            cursor.execute(query, (latitude, tolerance, longitude, tolerance))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                return {
                    "blmid": result[0],
                    "latitude": float(result[1]),
                    "longitude": float(result[2]),
                }
            return None

        except Error as e:
            logger.error(f"Database query failed: {e}")
            return None

    def find_by_blmid(self, blmid: str) -> Optional[Dict]:
        """
        Query database for BLMID record.

        Args:
            blmid: BLMID to search for

        Returns:
            Dict with record or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = f"""
                SELECT {self.blmid_column}, {self.latitude_column}, {self.longitude_column}
                FROM {self.table_name}
                WHERE UPPER({self.blmid_column}) = UPPER(%s)
                LIMIT 1;
            """

            cursor.execute(query, (blmid,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                return {
                    "blmid": result[0],
                    "latitude": float(result[1]),
                    "longitude": float(result[2]),
                }
            return None

        except Error as e:
            logger.error(f"Database query failed: {e}")
            return None

    def get_all_records(self) -> List[Dict]:
        """
        Retrieve all records from database.

        Returns:
            List of records
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = f"""
                SELECT {self.blmid_column}, {self.latitude_column}, {self.longitude_column}
                FROM {self.table_name};
            """

            cursor.execute(query)
            results = cursor.fetchall()

            cursor.close()
            conn.close()

            return [
                {
                    "blmid": row[0],
                    "latitude": float(row[1]),
                    "longitude": float(row[2]),
                }
                for row in results
            ]

        except Error as e:
            logger.error(f"Database query failed: {e}")
            return []

    def close(self) -> None:
        """Close database connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")


class MockDatabase:
    """Mock database for testing without a live database."""

    def __init__(self, records: Optional[List[Dict]] = None):
        """
        Initialize mock database.

        Args:
            records: List of mock BLMID records
        """
        self.records = records or [
            {"blmid": "BLM001", "latitude": 40.7128, "longitude": -74.0060},
            {"blmid": "BLM002", "latitude": 51.5074, "longitude": -0.1278},
            {"blmid": "BLM003", "latitude": 48.8566, "longitude": 2.3522},
        ]

    def find_by_coordinates(
        self, latitude: float, longitude: float, tolerance: float = 0.0001
    ) -> Optional[Dict]:
        """Find by coordinates."""
        for record in self.records:
            if (
                abs(record["latitude"] - latitude) <= tolerance
                and abs(record["longitude"] - longitude) <= tolerance
            ):
                return record.copy()
        return None

    def find_by_blmid(self, blmid: str) -> Optional[Dict]:
        """Find by BLMID."""
        for record in self.records:
            if record["blmid"].upper() == blmid.upper():
                return record.copy()
        return None

    def get_all_records(self) -> List[Dict]:
        """Get all records."""
        return [r.copy() for r in self.records]

    def close(self) -> None:
        """Mock close method."""
        pass
