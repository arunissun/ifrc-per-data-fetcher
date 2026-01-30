"""
Fetch data from IFRC GO API endpoints and save to JSON files.
Mirrors the functionality of fetchData.js
"""
import json
import sys
from pathlib import Path

from utils.fetch_paginated_data import fetch_paginated_data
from utils.fetch_per_overview import fetch_per_overview

# API Endpoints
PER_STATUS_URL = 'https://goadmin.ifrc.org/api/v2/public-per-process-status/'
COUNTRIES_URL = 'https://goadmin.ifrc.org/api/v2/country/'
PER_PRIORITIZATION_URL = 'https://goadmin.ifrc.org/api/v2/public-per-prioritization/'
PER_ASSESSMENTS_URL = 'https://goadmin.ifrc.org/api/v2/public-per-assessment/'


def ensure_data_directory(data_dir: Path) -> None:
    """Ensure the data directory exists."""
    print('Checking data directory...')
    if data_dir.exists():
        print('Data directory exists')
    else:
        print('Creating data directory...')
        data_dir.mkdir(parents=True, exist_ok=True)
        print('Created data directory')


def fetch_data(target_dir: str = None) -> None:
    """
    Fetch all data from IFRC APIs and save to JSON files.
    
    Args:
        target_dir: Directory to save data files (default: ../data_python relative to script)
    """
    if target_dir is None:
        target_dir = Path(__file__).parent.parent / 'data_python'
    else:
        target_dir = Path(target_dir)
    
    ensure_data_directory(target_dir)
    
    print('Starting fetchData function...')
    try:
        print('Fetching PER status data...')
        per_status_data = fetch_paginated_data(PER_STATUS_URL)
        with open(target_dir / 'per-status.json', 'w', encoding='utf-8') as f:
            json.dump({'results': per_status_data}, f, indent=2)
        print('PER status data saved')
        
        print('Fetching countries data...')
        countries_data = fetch_paginated_data(COUNTRIES_URL)
        with open(target_dir / 'countries.json', 'w', encoding='utf-8') as f:
            json.dump({'results': countries_data}, f, indent=2)
        print('Countries data saved')
        
        print('Fetching prioritization data...')
        prioritization_data = fetch_paginated_data(PER_PRIORITIZATION_URL)
        with open(target_dir / 'prioritization.json', 'w', encoding='utf-8') as f:
            json.dump({'results': prioritization_data}, f, indent=2)
        print('Component prioritization data saved')
        
        print('Fetching assessment data...')
        assessment_data = fetch_paginated_data(PER_ASSESSMENTS_URL)
        with open(target_dir / 'per-assessments.json', 'w', encoding='utf-8') as f:
            json.dump({'results': assessment_data}, f, indent=2)
        print('Assessment data saved')
        
        # Fetch per-overview data (authenticated endpoint)
        print('Fetching PER overview data (authenticated)...')
        try:
            overview_data = fetch_per_overview()
            with open(target_dir / 'per-overview.json', 'w', encoding='utf-8') as f:
                json.dump({'results': overview_data}, f, indent=2)
            print('PER overview data saved')
        except Exception as overview_error:
            print(f'Warning: Failed to fetch per-overview data: {overview_error}')
            print('Continuing without per-overview data...')
        
        print('All data fetched successfully')
        
    except Exception as error:
        print(f'Error fetching data: {error}')
        raise


if __name__ == '__main__':
    # Get target directory from command line arguments
    target = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_data(target)
