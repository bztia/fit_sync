# fit_sync

I maintain three fitness accounts:
- Garmin US (Endure3) - Used for daily activity tracking
- Garmin China - Contains historical fitness data
- Coros China (Vertix) - Used specifically for trail running activities

The goal of this project is to synchronize data from both my Garmin US and Coros China accounts to my Garmin China account, creating a consolidated fitness history.

## Features
This is a command line tool written in Python that provides the following capabilities:

- Authenticates with multiple fitness accounts (Garmin US, Garmin China, Coros China) and maintains cached sessions, enabling automated daily execution through Jenkins jobs
- Lists activities from source accounts with comprehensive filtering options by date, activity type, and additional parameters
- Downloads FIT files from source accounts using a simple human-readable index system, making it easy to identify and manage specific activities
- Caches activity information to minimize network requests and improve performance
- Downloads FIT files from source accounts and stores them efficiently in a local cache directory. Files are organized using a human-readable structure based on activity type and date, rather than complex identifiers like UUIDs or long string IDs, making manual browsing more intuitive.
- Uploads FIT files to destination accounts while intelligently detecting and managing conflicts with existing activities based on precise timestamp information
- Allows users to define custom synchronization rules between accounts (including sync direction, activity type filtering, conflict resolution strategies, etc.)
- Provides options to clear cached information through command-line arguments
- Features an extensible architecture that supports integration with additional fitness platforms and regional variants
- All account information is securely stored in the ~/.fit_sync/ directory and is never committed to the repository.

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fit_sync.git
   cd fit_sync
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create configuration directory:
   ```bash
   mkdir -p ~/.fit_sync
   ```

## Configuration

Create a folder `~/.fit_sync/` and put the configuration file `config.json` in it. A sample configuration file is provided in the project repository as `config.json`, and you can use it as a template to create your own configuration file.

### Configuration Structure

The configuration file has the following structure:
```
config.json
├── accounts                 # Login credentials for platforms
│   ├── garmin_us            # Garmin US account configuration
│   ├── garmin_cn            # Garmin China account configuration
│   └── coros_cn             # Coros China account configuration
├── sync_rules               # Array of data sync configurations
│   └── [rule objects]       # Each rule defines a sync direction and filters
└── cache                    # Performance optimization settings
    ├── max_age_days         # How long to keep cached data
    └── directory            # Where to store the cache
```

### Configuration Options

- **accounts**: Contains login credentials for each fitness platform
- **sync_rules**: Defines synchronization behavior between accounts
  - **source**: The account to copy activities from
  - **destination**: The account to copy activities to
  - **activity_types**: List of activity types to synchronize (empty list means all types)
  - **start_date**: Only synchronize activities after this date (format: YYYY-MM-DD)
  - **conflict_strategy**: How to handle existing activities ("skip_existing" or "replace_existing")
- **cache**: Controls caching behavior
  - **max_age_days**: Number of days to keep cached data
  - **directory**: Where to store cached data and FIT files

### Security Notes
- The config.json file contains sensitive login information. Never share it or commit it to a repository.
- Ensure the ~/.fit_sync directory has appropriate permissions (700 recommended).
- Consider using a password manager to generate and store unique passwords for your fitness accounts.

## Usage

### Basic Commands

```bash
# Authenticate with all accounts (first-time setup)
python -m fit_sync auth

# List activities from Garmin US account
python -m fit_sync list --account garmin_us --limit 10

# List activities from Coros China account
python -m fit_sync list --account coros_cn --limit 10 --activity-type trail_running

# Download a specific activity by index
python -m fit_sync download --account garmin_us --index 1

# Download a specific activity by ID (advanced usage)
python -m fit_sync download --account garmin_us --id 1234567890

# Download activity to a specific directory with human-readable filename
python -m fit_sync download --account garmin_us --index 1 --output-dir ~/Downloads/fit_files

# Sync activities based on rules in config.json
python -m fit_sync sync

# Sync activities with specific filters
python -m fit_sync sync --source garmin_us --destination garmin_cn --start-date 2023-03-01 --activity-type running,cycling

# Clear cached data
python -m fit_sync clear-cache
```

### Command Options

#### Common Options
- `--verbose`, `-v`: Enable verbose logging
- `--config PATH`: Specify an alternative configuration file

#### List Command
- `--account`: Account to list activities from
- `--limit N`: Maximum number of activities to display
- `--activity-type TYPE`: Filter by activity type
- `--start-date DATE`: Only show activities after date (YYYY-MM-DD)
- `--end-date DATE`: Only show activities before date (YYYY-MM-DD)

#### Download Command
- `--account`: Account to download activities from (required)
- `--index N`: Index of the activity to download (as shown in list command)
- `--id ID`: ID of the activity to download (advanced usage)
- `--output-dir DIR`: Directory to save downloaded files
- `--activity-type TYPE`: Filter by activity type
- `--start-date DATE`: Only consider activities after date (YYYY-MM-DD)
- `--end-date DATE`: Only consider activities before date (YYYY-MM-DD)
- `--limit N`: Maximum number of activities to consider

#### Sync Command
- `--source`: Override source account from config
- `--destination`: Override destination account from config
- `--dry-run`: Preview sync operations without making changes
- `--force`: Force sync even for activities that appear to be duplicates
- `--activity-type TYPE1,TYPE2`: Comma-separated list of activity types to sync
- `--start-date DATE`: Only sync activities after date (YYYY-MM-DD)
- `--end-date DATE`: Only sync activities before date (YYYY-MM-DD)

## Troubleshooting

### Authentication Issues
- Ensure your credentials in config.json are correct
- Check network connectivity to the fitness platforms
- For persistent issues, try clearing the authentication cache:
  ```bash
  python -m fit_sync clear-cache --auth-only
  ```

### Sync Problems
- Enable verbose logging with `-v` to get detailed error information
- Verify that your account has the necessary permissions
- For Garmin China issues, ensure your VPN or network connection can access China-based services

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



