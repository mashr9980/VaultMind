#!/usr/bin/env python3
"""
PostgreSQL Database Backup Script
Creates a complete dump of database with schema and data
"""

import subprocess
import os
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLBackup:
    def __init__(self, host='localhost', port='5432', username='postgres', password='', database='', pg_bin_path=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.pg_bin_path = pg_bin_path or self._find_pg_bin_path()
        
    def _find_pg_bin_path(self):
        """
        Find PostgreSQL bin directory on Windows
        """
        import platform
        if platform.system() == 'Windows':
            # Common PostgreSQL installation paths on Windows
            possible_paths = [
                r'C:\Program Files\PostgreSQL\17\bin',
                r'C:\Program Files\PostgreSQL\16\bin',
                r'C:\Program Files\PostgreSQL\15\bin',
                r'C:\Program Files\PostgreSQL\14\bin',
                r'C:\Program Files (x86)\PostgreSQL\17\bin',
                r'C:\Program Files (x86)\PostgreSQL\16\bin',
                r'C:\Program Files (x86)\PostgreSQL\15\bin',
                r'C:\Program Files (x86)\PostgreSQL\14\bin',
            ]
            
            for path in possible_paths:
                if os.path.exists(os.path.join(path, 'pg_dump.exe')):
                    logger.info(f"Found PostgreSQL binaries at: {path}")
                    return path
            
            logger.warning("PostgreSQL binaries not found in common locations")
            logger.warning("Please specify pg_bin_path manually or add PostgreSQL to PATH")
            return None
        else:
            # On Linux/Mac, assume binaries are in PATH
            return None
        
    def create_dump(self, output_file=None, include_data=True, include_schema=True, compress=False):
        """
        Create a complete database dump
        
        Args:
            output_file (str): Output file path. If None, auto-generates with timestamp
            include_data (bool): Include table data in dump
            include_schema (bool): Include schema (structure) in dump
            compress (bool): Create compressed dump (custom format)
        
        Returns:
            str: Path to created dump file
        """
        
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = ".dump" if compress else ".sql"
            output_file = f"{self.database}_backup_{timestamp}{extension}"
        
        # Build pg_dump command
        pg_dump_exe = 'pg_dump'
        if self.pg_bin_path:
            pg_dump_exe = os.path.join(self.pg_bin_path, 'pg_dump.exe' if os.name == 'nt' else 'pg_dump')
        
        cmd = [
            pg_dump_exe,
            '-h', self.host,
            '-p', self.port,
            '-U', self.username,
            '-d', self.database,
            '-v',  # Verbose output
            '--no-password'  # Don't prompt for password
        ]
        
        # Add format options
        if compress:
            cmd.extend(['-F', 'c'])  # Custom compressed format
        else:
            cmd.extend(['-f', output_file])  # Plain SQL format
            
        # Schema and data options
        if include_schema and include_data:
            pass  # Default behavior
        elif include_schema and not include_data:
            cmd.append('--schema-only')
        elif include_data and not include_schema:
            cmd.append('--data-only')
        else:
            logger.error("Must include either schema or data or both")
            return None
            
        # Additional options for complete backup
        cmd.extend([
            '--create',  # Include CREATE DATABASE statement
            '--clean',   # Include DROP statements
            '--if-exists',  # Use IF EXISTS with DROP statements
            '--no-owner',   # Don't set ownership
            '--no-privileges',  # Don't dump privileges
            '--encoding=UTF8'   # Set encoding
        ])
        
        # For compressed format, redirect output
        if compress:
            cmd.extend(['-f', output_file])
        
        try:
            # Set password environment variable if provided
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
            
            logger.info(f"Starting backup of database '{self.database}'...")
            logger.info(f"Output file: {output_file}")
            
            # Execute pg_dump
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # For non-compressed format, write output to file if not already done
            if not compress and not any('-f' in str(arg) for arg in cmd):
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
            
            # Check if file was created successfully
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"Backup completed successfully!")
                logger.info(f"File: {output_file}")
                logger.info(f"Size: {file_size:,} bytes")
                return output_file
            else:
                logger.error("Backup file was not created")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during backup: {str(e)}")
            return None
    
    def backup_all_databases(self, output_dir="backups"):
        """
        Backup all databases (excluding system databases)
        
        Args:
            output_dir (str): Directory to store backup files
        
        Returns:
            list: List of created backup files
        """
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get list of databases
        try:
            psql_exe = 'psql'
            if self.pg_bin_path:
                psql_exe = os.path.join(self.pg_bin_path, 'psql.exe' if os.name == 'nt' else 'psql')
            
            cmd = [
                psql_exe,
                '-h', self.host,
                '-p', self.port,
                '-U', self.username,
                '-t',  # Tuples only (no headers)
                '-c', "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1');"
            ]
            
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
                
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            databases = [db.strip() for db in result.stdout.split('\n') if db.strip()]
            
            backup_files = []
            for db in databases:
                logger.info(f"Backing up database: {db}")
                self.database = db
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(output_dir, f"{db}_backup_{timestamp}.sql")
                
                backup_file = self.create_dump(output_file)
                if backup_file:
                    backup_files.append(backup_file)
                    
            return backup_files
            
        except Exception as e:
            logger.error(f"Error getting database list: {str(e)}")
            return []

def main():
    """Example usage of the backup script"""
    
    # Configuration - modify these values
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'username': 'postgres',
        'password': '123',  # Set your password here
        'database': 'knowledge_base_db',  # Set your database name here
        'pg_bin_path': r'C:\Program Files\PostgreSQL\17\bin'  # Specify PostgreSQL bin path for Windows
    }
    
    # Create backup instance
    backup = PostgreSQLBackup(**DB_CONFIG)
    
    # Example 1: Create a standard SQL dump
    print("Creating standard SQL dump...")
    sql_dump = backup.create_dump(
        output_file="my_database_backup.sql",
        include_data=True,
        include_schema=True,
        compress=False
    )
    
    if sql_dump:
        print(f"SQL dump created: {sql_dump}")
    
    # Example 2: Create compressed dump
    print("\nCreating compressed dump...")
    compressed_dump = backup.create_dump(
        output_file="my_database_backup.dump",
        include_data=True,
        include_schema=True,
        compress=True
    )
    
    if compressed_dump:
        print(f"Compressed dump created: {compressed_dump}")
    
    # Example 3: Schema only backup
    print("\nCreating schema-only backup...")
    schema_dump = backup.create_dump(
        output_file="my_database_schema.sql",
        include_data=False,
        include_schema=True,
        compress=False
    )
    
    if schema_dump:
        print(f"Schema dump created: {schema_dump}")

if __name__ == "__main__":
    main()