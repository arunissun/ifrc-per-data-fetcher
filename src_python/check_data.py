"""
Analyze and validate the processed data files.
Mirrors the functionality of checkData.js
"""
import json
import sys
from pathlib import Path


def analyze_assessments(file_path: Path) -> None:
    """Analyze per-assessments.json file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data['results']
    total_assessments = len(results)
    with_component_responses = 0
    without_component_responses = 0
    
    for assessment in results:
        has_component_responses = any(
            area.get('component_responses') and len(area['component_responses']) > 0
            for area in assessment.get('area_responses', [])
        )
        
        if has_component_responses:
            with_component_responses += 1
        else:
            without_component_responses += 1
    
    print(f'Total Assessment IDs: {total_assessments}')
    print(f'Assessments with component_responses: {with_component_responses}')
    print(f'Assessments without component_responses: {without_component_responses}')


def analyze_status(file_path: Path) -> None:
    """Analyze per-status.json file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data['results']
    total_assessments = len(results)
    unique_countries = len(set(assessment.get('country') for assessment in results))
    
    print(f'Total Assessment IDs in per-status.json: {total_assessments}')
    print(f'Unique Countries in per-status.json: {unique_countries}')


def analyze_map_data(file_path: Path) -> None:
    """Analyze map-data.json file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    unique_countries = len(set(item.get('country_id') for item in data))
    total_assessments = len(data)
    
    print(f'Total Assessments in map-data.json: {total_assessments}')
    print(f'Unique Countries in map-data.json: {unique_countries}')


def analyze_processed_assessments(file_path: Path) -> None:
    """Analyze per-assessments-processed.json file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_assessments = len(data['results'])
    
    print(f'Total Assessments in per-assessments-processed.json: {total_assessments}')


def analyze_dashboard_data(file_path: Path) -> None:
    """Analyze per-dashboard-data.json file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assessments = data['assessments'][0]['assessments']
    
    unique_assessments = len(set(a.get('assessment_id') for a in assessments))
    unique_countries = len(set(a.get('country_id') for a in assessments))
    
    print(f'Total Assessment IDs in per-dashboard-data.json: {unique_assessments}')
    print(f'Unique Countries in per-dashboard-data.json: {unique_countries}')


def check_data(target_dir: str = None) -> None:
    """
    Run all data analysis checks.
    
    Args:
        target_dir: Directory containing data files (default: ../data_python)
    """
    if target_dir is None:
        target_dir = Path(__file__).parent.parent / 'data_python'
    else:
        target_dir = Path(target_dir)
    
    print(f'\n=== Analyzing data in: {target_dir} ===\n')
    
    # Run all analysis functions
    analyze_assessments(target_dir / 'per-assessments.json')
    print()
    analyze_status(target_dir / 'per-status.json')
    print()
    analyze_map_data(target_dir / 'map-data.json')
    print()
    analyze_processed_assessments(target_dir / 'per-assessments-processed.json')
    print()
    analyze_dashboard_data(target_dir / 'per-dashboard-data.json')


if __name__ == '__main__':
    # Get target directory from command line arguments
    target = sys.argv[1] if len(sys.argv) > 1 else None
    check_data(target)
