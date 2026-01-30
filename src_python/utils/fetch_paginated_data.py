"""
Fetch paginated data from IFRC GO API endpoints.
Handles pagination by following 'next' URLs until all data is retrieved.
"""
import requests


def fetch_paginated_data(base_url: str) -> list:
    """
    Fetch all pages of data from a paginated API endpoint.
    
    Args:
        base_url: The initial API URL to fetch from
        
    Returns:
        List of all results from all pages
    """
    all_results = []
    next_url = base_url
    
    print(f'Starting data fetch from: {base_url}')
    
    while next_url:
        try:
            print(f'Making request to: {next_url}')
            response = requests.get(
                next_url,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'IFRC-PER-Data-Fetcher',
                }
            )
            response.raise_for_status()
            
            print(f'Response status: {response.status_code}')
            
            data = response.json()
            
            if not data:
                print('No data in response')
                break
            
            results = data.get('results')
            next_url = data.get('next')
            count = data.get('count', 0)
            
            if results is None:
                print(f'No results in response data: {data}')
                break
            
            if not all_results:
                print(f'Total records to fetch: {count}')
            
            all_results.extend(results)
            print(f'Fetched {len(all_results)} of {count} records')
            
        except requests.exceptions.RequestException as error:
            print(f'Error details: {error}')
            if hasattr(error, 'response') and error.response is not None:
                print(f'Response error: status={error.response.status_code}, data={error.response.text}')
            raise
    
    return all_results
