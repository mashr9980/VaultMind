#!/usr/bin/env python3
"""
PostgreSQL Database Restore Script
Restores database from SQL dump files with exact data preservation
"""

import subprocess
import os
import sys
from datetime import datetime
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLRestore:
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
        
    def check_database_exists(self, database_name=None):
        """
        Check if database exists
        
        Args:
            database_name (str): Database name to check. Uses self.database if None
            
        Returns:
            bool: True if database exists
        """
        if database_name is None:
            database_name = self.database
            
        try:
            psql_exe = 'psql'
            if self.pg_bin_path:
                psql_exe = os.path.join(self.pg_bin_path, 'psql.exe' if os.name == 'nt' else 'psql')
                
            cmd = [
                psql_exe,
                '-h', self.host,
                '-p', self.port,
                '-U', self.username,
                '-t',
                '-c', f"SELECT 1 FROM pg_database WHERE datname='{database_name}';"
            ]
            
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
                
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            return result.stdout.strip() == '1'
            
        except Exception as e:
            logger.error(f"Error checking database existence: {str(e)}")
            return False
    
    def create_database(self, database_name=None, drop_if_exists=False):
        """
        Create a new database
        
        Args:
            database_name (str): Database name to create. Uses self.database if None
            drop_if_exists (bool): Drop database if it already exists
            
        Returns:
            bool: True if database was created successfully
        """
        if database_name is None:
            database_name = self.database
            
        try:
            # Connect to postgres database to create new database
            psql_exe = 'psql'
            if self.pg_bin_path:
                psql_exe = os.path.join(self.pg_bin_path, 'psql.exe' if os.name == 'nt' else 'psql')
                
            cmd_base = [
                psql_exe,
                '-h', self.host,
                '-p', self.port,
                '-U', self.username,
                '-d', 'postgres'  # Connect to postgres database
            ]
            
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
            
            # Drop database if requested and exists
            if drop_if_exists and self.check_database_exists(database_name):
                logger.info(f"Dropping existing database '{database_name}'...")
                
                # Terminate connections to the database
                terminate_cmd = cmd_base + ['-c', f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{database_name}'
                    AND pid <> pg_backend_pid();
                """]
                
                subprocess.run(terminate_cmd, env=env, capture_output=True, text=True)
                time.sleep(1)  # Wait a moment for connections to close
                
                # Drop database
                drop_cmd = cmd_base + ['-c', f'DROP DATABASE IF EXISTS "{database_name}";']
                result = subprocess.run(drop_cmd, env=env, capture_output=True, text=True, check=True)
                logger.info(f"Database '{database_name}' dropped successfully")
            
            # Create database
            if not self.check_database_exists(database_name):
                logger.info(f"Creating database '{database_name}'...")
                create_cmd = cmd_base + ['-c', f'CREATE DATABASE "{database_name}" WITH ENCODING = \'UTF8\';']
                result = subprocess.run(create_cmd, env=env, capture_output=True, text=True, check=True)
                logger.info(f"Database '{database_name}' created successfully")
                return True
            else:
                logger.info(f"Database '{database_name}' already exists")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create database: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating database: {str(e)}")
            return False
    
    def restore_from_sql(self, sql_file, target_database=None, create_db=False, drop_if_exists=False):
        """
        Restore database from SQL file
        
        Args:
            sql_file (str): Path to SQL dump file
            target_database (str): Target database name. Uses self.database if None
            create_db (bool): Create database if it doesn't exist
            drop_if_exists (bool): Drop and recreate database if it exists
            
        Returns:
            bool: True if restore was successful
        """
        if target_database is None:
            target_database = self.database
            
        if not os.path.exists(sql_file):
            logger.error(f"SQL file not found: {sql_file}")
            return False
        
        try:
            # Create database if requested
            if create_db:
                if not self.create_database(target_database, drop_if_exists):
                    logger.error("Failed to create target database")
                    return False
            
            # Check if target database exists
            if not self.check_database_exists(target_database):
                logger.error(f"Target database '{target_database}' does not exist")
                logger.info("Use create_db=True to create it automatically")
                return False
            
            logger.info(f"Starting restore from '{sql_file}' to database '{target_database}'...")
            
            # Build psql command for restore
            psql_exe = 'psql'
            if self.pg_bin_path:
                psql_exe = os.path.join(self.pg_bin_path, 'psql.exe' if os.name == 'nt' else 'psql')
            
            cmd = [
                psql_exe,
                '-h', self.host,
                '-p', self.port,
                '-U', self.username,
                '-d', target_database,
                '-f', sql_file,
                '-v', 'ON_ERROR_STOP=1',  # Stop on first error
                '--no-password'
            ]
            
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
            
            # Execute restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Database restore completed successfully!")
            logger.info(f"Restored to database: {target_database}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during restore: {str(e)}")
            return False
    
    def restore_from_dump(self, dump_file, target_database=None, create_db=False, drop_if_exists=False):
        """
        Restore database from compressed dump file (pg_restore)
        
        Args:
            dump_file (str): Path to compressed dump file
            target_database (str): Target database name. Uses self.database if None
            create_db (bool): Create database if it doesn't exist
            drop_if_exists (bool): Drop and recreate database if it exists
            
        Returns:
            bool: True if restore was successful
        """
        if target_database is None:
            target_database = self.database
            
        if not os.path.exists(dump_file):
            logger.error(f"Dump file not found: {dump_file}")
            return False
        
        try:
            # Create database if requested
            if create_db:
                if not self.create_database(target_database, drop_if_exists):
                    logger.error("Failed to create target database")
                    return False
            
            # Check if target database exists
            if not self.check_database_exists(target_database):
                logger.error(f"Target database '{target_database}' does not exist")
                logger.info("Use create_db=True to create it automatically")
                return False
            
            logger.info(f"Starting restore from '{dump_file}' to database '{target_database}'...")
            
            # Build pg_restore command
            pg_restore_exe = 'pg_restore'
            if self.pg_bin_path:
                pg_restore_exe = os.path.join(self.pg_bin_path, 'pg_restore.exe' if os.name == 'nt' else 'pg_restore')
            
            cmd = [
                pg_restore_exe,
                '-h', self.host,
                '-p', self.port,
                '-U', self.username,
                '-d', target_database,
                '-v',  # Verbose
                '--clean',  # Clean before restore
                '--if-exists',  # Use IF EXISTS with clean
                '--no-owner',  # Don't set ownership
                '--no-privileges',  # Don't restore privileges
                dump_file
            ]
            
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
            
            # Execute restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Database restore completed successfully!")
            logger.info(f"Restored to database: {target_database}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during restore: {str(e)}")
            return False
    
    def verify_restore(self, database_name=None):
        """
        Verify restore by checking basic database statistics
        
        Args:
            database_name (str): Database name to verify. Uses self.database if None
            
        Returns:
            dict: Dictionary with verification results
        """
        if database_name is None:
            database_name = self.database
            
        try:
            psql_exe = 'psql'
            if self.pg_bin_path:
                psql_exe = os.path.join(self.pg_bin_path, 'psql.exe' if os.name == 'nt' else 'psql')
                
            cmd = [
                psql_exe,
                '-h', self.host,
                '-p', self.port,
                '-U', self.username,
                '-d', database_name,
                '-t',
                '-c', '''
                SELECT 
                    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count,
                    (SELECT count(*) FROM information_schema.views WHERE table_schema = 'public') as view_count,
                    (SELECT count(*) FROM information_schema.routines WHERE routine_schema = 'public') as function_count;
                '''
            ]
            
            env = os.environ.copy()
            if self.password:
                env['PGPASSWORD'] = self.password
                
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            # Parse result
            output = result.stdout.strip().split('|')
            if len(output) >= 3:
                verification = {
                    'database': database_name,
                    'table_count': int(output[0].strip()),
                    'view_count': int(output[1].strip()),
                    'function_count': int(output[2].strip()),
                    'status': 'success'
                }
                
                logger.info(f"Verification results for '{database_name}':")
                logger.info(f"  Tables: {verification['table_count']}")
                logger.info(f"  Views: {verification['view_count']}")
                logger.info(f"  Functions: {verification['function_count']}")
                
                return verification
            else:
                return {'status': 'error', 'message': 'Could not parse verification results'}
                
        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            return {'status': 'error', 'message': str(e)}

def main():
    """Example usage of the restore script"""
    
    # Configuration - modify these values
    DB_CONFIG = {
        'host': 'localhost',
        'port': '5432',
        'username': 'postgres',
        'password': '123',  # Set your password here
        'database': 'restored_database_name',  # Set target database name here
        'pg_bin_path': r'C:\Program Files\PostgreSQL\17\bin'  # Specify PostgreSQL bin path for Windows
    }
    
    # Create restore instance
    restore = PostgreSQLRestore(**DB_CONFIG)
    
    # Example 1: Restore from SQL file (create database if needed)
    sql_file = "my_database_backup.sql"  # Path to your backup file
    
    if os.path.exists(sql_file):
        print(f"Restoring from SQL file: {sql_file}")
        success = restore.restore_from_sql(
            sql_file=sql_file,
            target_database=DB_CONFIG['database'],
            create_db=True,  # Create database if it doesn't exist
            drop_if_exists=True  # Drop existing database if present
        )
        
        if success:
            print("SQL restore completed successfully!")
            # Verify the restore
            verification = restore.verify_restore()
            print(f"Verification: {verification}")
        else:
            print("SQL restore failed!")
    
    # Example 2: Restore from compressed dump file
    dump_file = "my_database_backup.dump"  # Path to your compressed backup
    
    if os.path.exists(dump_file):
        print(f"\nRestoring from dump file: {dump_file}")
        success = restore.restore_from_dump(
            dump_file=dump_file,
            target_database=DB_CONFIG['database'] + "_from_dump",
            create_db=True,
            drop_if_exists=True
        )
        
        if success:
            print("Dump restore completed successfully!")
        else:
            print("Dump restore failed!")

if __name__ == "__main__":
    main()