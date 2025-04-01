#!/usr/bin/env python3
"""
Command-line interface for fit_sync.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List

from .sync import SyncManager

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Sync fitness activities between platforms')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Auth command
    auth_parser = subparsers.add_parser('auth', help='Authenticate with fitness platforms')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List activities')
    list_parser.add_argument('--account', help='Account to list activities from')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum number of activities to display')
    list_parser.add_argument('--activity-type', help='Filter by activity type')
    list_parser.add_argument('--start-date', help='Only show activities after date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='Only show activities before date (YYYY-MM-DD)')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download activity FIT files')
    download_parser.add_argument('--account', required=True, help='Account to download activities from')
    download_parser.add_argument('--index', type=int, help='Index of the activity to download (from list command)')
    download_parser.add_argument('--id', help='ID of the activity to download (advanced users)')
    download_parser.add_argument('--output-dir', help='Directory to save downloaded files')
    download_parser.add_argument('--activity-type', help='Filter by activity type')
    download_parser.add_argument('--start-date', help='Only consider activities after date (YYYY-MM-DD)')
    download_parser.add_argument('--end-date', help='Only consider activities before date (YYYY-MM-DD)')
    download_parser.add_argument('--limit', type=int, default=10, help='Maximum number of activities to consider')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync activities between platforms')
    sync_parser.add_argument('--source', help='Override source account from config')
    sync_parser.add_argument('--destination', help='Override destination account from config')
    sync_parser.add_argument('--dry-run', action='store_true', help='Preview sync operations without making changes')
    sync_parser.add_argument('--force', action='store_true', help='Force sync even for activities that appear to be duplicates')
    sync_parser.add_argument('--activity-type', help='Comma-separated list of activity types to sync')
    sync_parser.add_argument('--start-date', help='Only sync activities after date (YYYY-MM-DD)')
    sync_parser.add_argument('--end-date', help='Only sync activities before date (YYYY-MM-DD)')
    
    # Clear cache command
    clear_cache_parser = subparsers.add_parser('clear-cache', help='Clear cached data')
    clear_cache_parser.add_argument('--auth-only', action='store_true', help='Only clear authentication cache')
    
    # Common options
    for subparser in [auth_parser, list_parser, download_parser, sync_parser, clear_cache_parser]:
        subparser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
        subparser.add_argument('--config', help='Specify an alternative configuration file')
    
    args = parser.parse_args()
    
    # Ensure a command was specified
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config_path = args.config or os.path.expanduser('~/.fit_sync/config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        logger.error("Please create a configuration file as described in the documentation.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Configuration file at {config_path} is not valid JSON")
        sys.exit(1)
    
    # Create sync manager
    sync_manager = SyncManager(config)
    
    # Execute the requested command
    if args.command == 'auth':
        logger.info("Authenticating with fitness platforms...")
        if sync_manager.authenticate_all():
            logger.info("Authentication successful for all platforms")
            sys.exit(0)
        else:
            logger.error("Authentication failed for one or more platforms")
            sys.exit(1)
    
    elif args.command == 'list':
        account = args.account
        if not account:
            logger.error("Please specify an account with --account")
            sys.exit(1)
            
        if account not in sync_manager.platforms:
            logger.error(f"Account {account} not configured")
            sys.exit(1)
            
        platform = sync_manager.platforms[account]
        # Authenticate
        if not platform.authenticate():
            logger.error(f"Authentication failed for {account}")
            sys.exit(1)
            
        # List activities
        activities = platform.list_activities(
            limit=args.limit,
            activity_type=args.activity_type,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        if not activities:
            logger.info(f"No activities found for {account}")
            sys.exit(0)
            
        # Display activities
        print(f"\nActivities from {account}:")
        print("-" * 80)
        for i, activity in enumerate(activities):
            print(f"{i+1}. {activity.get('startTime', 'Unknown')} - "
                  f"{activity.get('activityType', 'Unknown')} - "
                  f"{activity.get('duration', 'Unknown')} - "
                  f"{activity.get('distance', 'Unknown')} - "
                  f"ID: {activity.get('id', 'Unknown')}")
        print("-" * 80)
        sys.exit(0)
    
    elif args.command == 'download':
        account = args.account
        if account not in sync_manager.platforms:
            logger.error(f"Account {account} not configured")
            sys.exit(1)
        
        # If direct ID is provided, download that activity
        if args.id:
            output_dir = args.output_dir or os.getcwd()
            
            # Download directly using SyncManager
            fit_file = sync_manager.download_activity(
                account, 
                args.id,
                output_dir=output_dir
            )
            
            if fit_file:
                logger.info(f"Downloaded activity {args.id} to {fit_file}")
                sys.exit(0)
            else:
                logger.error(f"Failed to download activity {args.id}")
                sys.exit(1)
        
        # Otherwise, authenticate and list activities for download by index
        platform = sync_manager.platforms[account]
        if not platform.authenticate():
            logger.error(f"Authentication failed for {account}")
            sys.exit(1)
            
        activities = platform.list_activities(
            limit=args.limit,
            activity_type=args.activity_type,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        if not activities:
            logger.info(f"No activities found for {account}")
            sys.exit(0)
            
        # If no index provided, display activities and exit
        if args.index is None:
            print(f"\nActivities from {account}:")
            print("-" * 80)
            for i, activity in enumerate(activities):
                print(f"{i+1}. {activity.get('startTime', 'Unknown')} - "
                      f"{activity.get('activityType', 'Unknown')} - "
                      f"{activity.get('duration', 'Unknown')} - "
                      f"{activity.get('distance', 'Unknown')} - "
                      f"ID: {activity.get('id', 'Unknown')}")
            print("-" * 80)
            print("Use --index <number> to download a specific activity")
            sys.exit(0)
            
        # Download the activity at the specified index
        if 1 <= args.index <= len(activities):
            activity = activities[args.index - 1]
            activity_id = activity.get('id')
            
            if not activity_id:
                logger.error(f"No ID found for activity at index {args.index}")
                sys.exit(1)
            
            # Create a human-readable filename if output directory is specified
            output_filename = None
            if args.output_dir:
                activity_date = activity.get('startTime', '').split(' ')[0].replace('-', '')
                activity_type = activity.get('activityType', 'activity')
                output_filename = f"{activity_date}_{activity_type}_{args.index}.fit"
            
            # Download using SyncManager
            fit_file = sync_manager.download_activity(
                account,
                activity_id,
                output_dir=args.output_dir,
                output_filename=output_filename
            )
            
            if fit_file:
                logger.info(f"Downloaded activity to {fit_file}")
                sys.exit(0)
            else:
                logger.error(f"Failed to download activity at index {args.index}")
                sys.exit(1)
        else:
            logger.error(f"Invalid index {args.index}. Valid range: 1-{len(activities)}")
            sys.exit(1)
    
    elif args.command == 'sync':
        # Authenticate with all platforms
        if not sync_manager.authenticate_all():
            logger.error("Authentication failed, cannot sync")
            sys.exit(1)
            
        # Parse activity types if provided
        activity_types = None
        if args.activity_type:
            activity_types = args.activity_type.split(',')
            
        # Perform sync
        synced_count = sync_manager.sync(
            source=args.source,
            destination=args.destination,
            activity_types=activity_types,
            start_date=args.start_date,
            end_date=args.end_date,
            dry_run=args.dry_run,
            force=args.force
        )
        
        logger.info(f"Sync completed. {synced_count} activities synchronized.")
        sys.exit(0)
    
    elif args.command == 'clear-cache':
        cache_dir = Path(config.get('cache', {}).get('directory', '~/.fit_sync/cache')).expanduser()
        if args.auth_only:
            auth_cache = cache_dir / 'auth'
            if auth_cache.exists():
                import shutil
                shutil.rmtree(auth_cache)
                logger.info(f"Cleared authentication cache at {auth_cache}")
            else:
                logger.info(f"No authentication cache found at {auth_cache}")
        else:
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleared all cached data at {cache_dir}")
            else:
                logger.info(f"No cache directory found at {cache_dir}")
        sys.exit(0)

if __name__ == '__main__':
    main() 