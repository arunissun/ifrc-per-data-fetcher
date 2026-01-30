"""
Fetch per-overview data with authentication.

This module fetches data from the /api/v2/per-overview/ endpoint,
which requires authentication. It provides `assess_*_of_country` fields.

Merge strategy:
  per-overview.id → per-status.id → per-status.assessment → per-assessments.id
"""
import json
import sys
from pathlib import Path

import requests


PER_OVERVIEW_URL = 'https://goadmin.ifrc.org/api/v2/per-overview/'

# Token for authentication
API_TOKEN = '2670a81f5e7146b16e7f9efba63f36b3d7ff97a8'


def fetch_authenticated_paginated_data(base_url: str, token: str) -> list:
    """
    Fetch paginated data from an authenticated API endpoint.
    
    Args:
        base_url: The API URL to fetch from
        token: The authentication token
        
    Returns:
        List of all results from all pages
    """
    all_results = []
    next_url = base_url
    
    print(f'Starting authenticated data fetch from: {base_url}')
    
    while next_url:
        try:
            print(f'Making authenticated request to: {next_url}')
            response = requests.get(
                next_url,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'IFRC-PER-Data-Fetcher',
                    'Authorization': f'Token {token}',
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            count = data.get('count', 0)
            
            if not all_results:
                print(f'Total records to fetch: {count}')
            
            all_results.extend(results)
            print(f'Fetched {len(all_results)} of {count} records')
            
            next_url = data.get('next')
            
        except requests.exceptions.RequestException as error:
            print(f'Error fetching data: {error}')
            raise
    
    return all_results


def fetch_per_overview(token: str = None) -> list:
    """
    Fetch PER Overview data with authentication.
    
    Args:
        token: Optional token, defaults to hardcoded token
        
    Returns:
        List of overview records
    """
    token = token or API_TOKEN
    
    print('Fetching PER Overview data (authenticated)...')
    overview_data = fetch_authenticated_paginated_data(PER_OVERVIEW_URL, token)
    print(f'Fetched {len(overview_data)} overview records')
    
    return overview_data


if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else 'data_python'
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    try:
        data = fetch_per_overview()
        output_file = target_path / 'per-overview.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'results': data}, f, indent=2)
        print(f'Saved to {output_file}')
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)
