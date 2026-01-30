"""
Process IFRC PER data and generate dashboard-ready JSON files.
Mirrors the functionality of processData.js with migration_considerations included.
"""
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


def ensure_directory_exists(target_dir: Path) -> None:
    """Ensure the target directory exists."""
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)


def contains_affirmative_word(text: str) -> bool:
    """
    Check if text contains affirmative words in English or Spanish.
    
    Args:
        text: The text to check
        
    Returns:
        True if text contains 'yes', 'sí', or 'si'
    """
    if not text or not isinstance(text, str):
        return False
    
    # List of affirmative words in English and Spanish
    affirmative_words = ['yes', 'sí', 'si']
    
    # Normalize text to lower case and remove accents for comparison
    normalized_text = text.lower()
    # Remove diacritics (accents)
    normalized_text = unicodedata.normalize('NFD', normalized_text)
    normalized_text = ''.join(
        char for char in normalized_text 
        if unicodedata.category(char) != 'Mn'
    )
    
    return any(word in normalized_text for word in affirmative_words)


def process_data(target_dir: str = None) -> None:
    """
    Process downloaded data and generate dashboard-ready JSON files.
    
    Args:
        target_dir: Directory containing input files and for output (default: ../data_python)
    """
    if target_dir is None:
        target_dir = Path(__file__).parent.parent / 'data_python'
    else:
        target_dir = Path(target_dir)
    
    try:
        print('\n=== Starting Data Processing ===')
        print(f'Target directory: {target_dir}')
        
        # Ensure the directory exists before proceeding
        ensure_directory_exists(target_dir)
        
        # Update last update timestamp
        print('\nUpdating timestamp...')
        with open(target_dir / 'last-update.json', 'w', encoding='utf-8') as f:
            json.dump({'lastUpdate': datetime.now().isoformat() + 'Z'}, f, indent=2)
        
        # Read the downloaded files
        print('\nReading input files...')
        print('- Reading per-status.json')
        with open(target_dir / 'per-status.json', 'r', encoding='utf-8') as f:
            per_status_data = json.load(f)
        
        print('- Reading countries.json')
        with open(target_dir / 'countries.json', 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        print('- Reading prioritization.json')
        with open(target_dir / 'prioritization.json', 'r', encoding='utf-8') as f:
            prioritization_data = json.load(f)
        
        print('- Reading per-assessments.json')
        with open(target_dir / 'per-assessments.json', 'r', encoding='utf-8') as f:
            assessments = json.load(f)
        
        # Try to read per-overview data (optional, requires authentication to fetch)
        per_overview_data = {'results': []}
        try:
            print('- Reading per-overview.json')
            with open(target_dir / 'per-overview.json', 'r', encoding='utf-8') as f:
                per_overview_data = json.load(f)
        except FileNotFoundError:
            print('- per-overview.json not found (optional file)')
        
        print('\nInput Data Summary:')
        print(f'- Total input assessments: {len(assessments["results"])}')
        print(f'- Total status assessments: {len(per_status_data["results"])}')
        print(f'- Total countries: {len(countries_data["results"])}')
        print(f'- Total prioritization items: {len(prioritization_data["results"])}')
        print(f'- Total overview items: {len(per_overview_data["results"])}')
        
        # Create a lookup map for per-overview data (keyed by id, same as per-status.id)
        # This allows us to merge assess_*_of_country fields
        overview_map = {
            overview['id']: {
                'assess_preparedness_of_country': overview.get('assess_preparedness_of_country'),
                'assess_urban_aspect_of_country': overview.get('assess_urban_aspect_of_country'),
                'assess_climate_environment_of_country': overview.get('assess_climate_environment_of_country'),
                'assess_migration_aspect_of_country': overview.get('assess_migration_aspect_of_country'),
            }
            for overview in per_overview_data['results']
        }
        
        # Create a lookup map for countries
        country_map = {
            country['iso3']: {
                'centroid': country.get('centroid'),
                'iso3': country['iso3'],
                'region': country.get('region'),
                'name': country.get('name'),
            }
            for country in countries_data['results']
        }
        
        # Create a components description lookup
        component_descriptions = {}
        for item in prioritization_data['results']:
            for response in item.get('prioritized_action_responses', []):
                component = response.get('component_details', {})
                component_id = component.get('id')
                if component_id:
                    component_descriptions[component_id] = {
                        'componentTitle': component.get('title'),
                        'areaTitle': component.get('area', {}).get('title'),
                        'description': component.get('description'),
                    }
        
        # Create a simplified prioritization lookup
        prioritization_map = {}
        for item in prioritization_data['results']:
            overview_id = item.get('overview')
            components = []
            for response in item.get('prioritized_action_responses', []):
                component_details = response.get('component_details', {})
                components.append({
                    'componentId': response.get('component'),
                    'componentTitle': component_details.get('title'),
                    'areaTitle': component_details.get('area', {}).get('title'),
                })
            prioritization_map[overview_id] = {'components': components}
        
        # Map region_id to region_name
        region_id_to_name_map = {
            0: 'Africa',
            1: 'Americas',
            2: 'Asia Pacific',
            3: 'Europe',
            4: 'MENA',
        }
        
        # Add area names mapping
        area_names = {
            1: 'Policy Strategy and Standards',
            2: 'Analysis and planning',
            3: 'Operational capacity',
            4: 'Coordination',
            5: 'Operations support',
        }
        
        # Process the assessments data
        processed_assessments = []
        for result in assessments['results']:
            processed_result = {
                'id': result['id'],
                'area_responses': []
            }
            
            for area_response in result.get('area_responses', []):
                processed_area = {
                    'id': area_response['id'],
                    'component_responses': []
                }
                
                for component_response in area_response.get('component_responses', []):
                    component_details = component_response.get('component_details') or {}
                    rating_details = component_response.get('rating_details') or {}
                    
                    simplified_component_details = {
                        'id': component_details.get('id'),
                        'component_num': component_details.get('component_num'),
                        'area': component_details.get('area'),
                        'title': component_details.get('title'),
                        'description': component_details.get('description'),
                    }
                    
                    simplified_rating_details = {
                        'id': rating_details.get('id'),
                        'value': rating_details.get('value'),
                        'title': rating_details.get('title'),
                    }
                    
                    # Extract the text fields
                    urban_considerations = component_response.get('urban_considerations')
                    epi_considerations = component_response.get('epi_considerations')
                    climate_environmental_considerations = component_response.get('climate_environmental_considerations')
                    migration_considerations = component_response.get('migration_considerations')
                    
                    # Create simplified boolean fields
                    urban_considerations_simplified = contains_affirmative_word(urban_considerations)
                    epi_considerations_simplified = contains_affirmative_word(epi_considerations)
                    climate_environmental_considerations_simplified = contains_affirmative_word(climate_environmental_considerations)
                    migration_considerations_simplified = contains_affirmative_word(migration_considerations)
                    
                    processed_component = {
                        'id': component_response['id'],
                        'component': component_response.get('component'),
                        'rating': component_response.get('rating'),
                        'rating_details': simplified_rating_details,
                        'component_details': simplified_component_details,
                        'urban_considerations': urban_considerations,
                        'epi_considerations': epi_considerations,
                        'climate_environmental_considerations': climate_environmental_considerations,
                        'migration_considerations': migration_considerations,
                        'urban_considerations_simplified': urban_considerations_simplified,
                        'epi_considerations_simplified': epi_considerations_simplified,
                        'climate_environmental_considerations_simplified': climate_environmental_considerations_simplified,
                        'migration_considerations_simplified': migration_considerations_simplified,
                        'notes': component_response.get('notes'),
                    }
                    
                    processed_area['component_responses'].append(processed_component)
                
                processed_result['area_responses'].append(processed_area)
            
            processed_assessments.append(processed_result)
        
        # Add dashboard assessments processing
        dashboard_assessments = []
        for assessment in assessments['results']:
            components = []
            
            for area_response in assessment.get('area_responses', []):
                for component_response in area_response.get('component_responses', []):
                    component_details = component_response.get('component_details') or {}
                    rating_details = component_response.get('rating_details') or {}
                    
                    components.append({
                        'component_id': component_response.get('component'),
                        'component_name': component_details.get('title', ''),
                        'component_num': component_details.get('component_num'),
                        'area_id': component_details.get('area'),
                        'area_name': area_names.get(component_details.get('area'), ''),
                        'rating_value': rating_details.get('value', 0),
                        'rating_title': rating_details.get('title', ''),
                    })
            
            dashboard_assessments.append({
                'assessment_id': assessment['id'],
                'components': components,
            })
        
        # Create a map from assessment ID to considerations booleans
        assessment_considerations_map = {}
        
        for assessment in processed_assessments:
            epi_considerations = False
            climate_environmental_considerations = False
            urban_considerations = False
            migration_considerations = False
            
            for area_response in assessment['area_responses']:
                for component_response in area_response['component_responses']:
                    if component_response.get('epi_considerations_simplified'):
                        epi_considerations = True
                    if component_response.get('climate_environmental_considerations_simplified'):
                        climate_environmental_considerations = True
                    if component_response.get('urban_considerations_simplified'):
                        urban_considerations = True
                    if component_response.get('migration_considerations_simplified'):
                        migration_considerations = True
            
            assessment_considerations_map[assessment['id']] = {
                'epi_considerations': epi_considerations,
                'climate_environmental_considerations': climate_environmental_considerations,
                'urban_considerations': urban_considerations,
                'migration_considerations': migration_considerations,
            }
        
        # Process and join the data based on iso3 code and include prioritization data
        joined_data = []
        for status in per_status_data['results']:
            country_details = status.get('country_details', {})
            country_iso3 = country_details.get('iso3') if country_details else None
            country_data = country_map.get(country_iso3, {})
            
            region_id = country_data.get('region') or (country_details.get('region') if country_details else None)
            prioritization = prioritization_map.get(status['id'], {'components': []})
            
            # Find dashboard assessment
            dashboard_assessment = {'components': []}
            for da in dashboard_assessments:
                if da['assessment_id'] == status.get('assessment'):
                    dashboard_assessment = da
                    break
            
            # Get considerations from the map
            considerations = assessment_considerations_map.get(
                status.get('assessment'),
                {
                    'epi_considerations': False,
                    'climate_environmental_considerations': False,
                    'urban_considerations': False,
                    'migration_considerations': False,
                }
            )
            
            # Get overview data for assess_*_of_country fields
            # per-overview.id matches per-status.id
            overview = overview_map.get(status['id'], {
                'assess_preparedness_of_country': None,
                'assess_urban_aspect_of_country': None,
                'assess_climate_environment_of_country': None,
                'assess_migration_aspect_of_country': None,
            })
            
            phase_display = status.get('phase_display', '')
            if phase_display == 'Action And Accountability':
                phase_display = 'Action & accountability'
            elif phase_display == 'WorkPlan':
                phase_display = 'Workplan'
            
            # Get centroid coordinates safely
            centroid = country_data.get('centroid') or {}
            coordinates = centroid.get('coordinates', [None, None]) if centroid else [None, None]
            
            joined_record = {
                'id': status['id'],
                'assessment_number': status.get('assessment_number'),
                'date_of_assessment': status.get('date_of_assessment'),
                'country_id': status.get('country'),
                'country_name': (country_details.get('name') if country_details else None) or country_data.get('name'),
                'phase': status.get('phase'),
                'phase_display': phase_display,
                'type_of_assessment': status.get('type_of_assessment'),
                'type_of_assessment_name': status.get('type_of_assessment_details', {}).get('name') if status.get('type_of_assessment_details') else None,
                'country_iso3': (country_details.get('iso3') if country_details else None) or country_data.get('iso3'),
                'region_id': region_id,
                'region_name': region_id_to_name_map.get(region_id),
                'latitude': coordinates[1] if len(coordinates) > 1 else None,
                'longitude': coordinates[0] if len(coordinates) > 0 else None,
                'updated_at': status.get('updated_at'),
                'prioritized_components': prioritization['components'],
                # Component-level considerations (aggregated from assessments)
                'epi_considerations': considerations['epi_considerations'],
                'climate_environmental_considerations': considerations['climate_environmental_considerations'],
                'urban_considerations': considerations['urban_considerations'],
                'migration_considerations': considerations['migration_considerations'],
                # Overview-level assess_*_of_country fields (from per-overview API)
                'assess_preparedness_of_country': overview['assess_preparedness_of_country'],
                'assess_urban_aspect_of_country': overview['assess_urban_aspect_of_country'],
                'assess_climate_environment_of_country': overview['assess_climate_environment_of_country'],
                'assess_migration_aspect_of_country': overview['assess_migration_aspect_of_country'],
                'components': dashboard_assessment['components'],
            }
            joined_data.append(joined_record)
        
        # Fix: When creating grouped data, don't filter out assessments without components
        grouped = []
        for assessment in joined_data:
            # Initialize empty components array if null
            components = assessment.get('components') or []
            
            # Always create at least one group entry even if no components
            if not components:
                empty_assessment = {
                    'assessment_id': assessment['id'],
                    'assessment_number': assessment['assessment_number'],
                    'country_id': assessment['country_id'],
                    'country_name': assessment['country_name'],
                    'region_id': assessment['region_id'],
                    'region_name': assessment['region_name'],
                    'date_of_assessment': assessment['date_of_assessment'],
                    'rating_value': None,
                    'rating_title': '',
                }
                
                # Add empty assessment to first component group or create new one
                if not grouped:
                    grouped.append({
                        'component_id': None,
                        'component_num': None,
                        'component_name': '',
                        'area_id': None,
                        'area_name': '',
                        'assessments': [empty_assessment],
                    })
                else:
                    grouped[0]['assessments'].append(empty_assessment)
            
            # Process components if they exist
            for component in components:
                component_id = component['component_id']
                existing_component = None
                for item in grouped:
                    if item['component_id'] == component_id:
                        existing_component = item
                        break
                
                if not existing_component:
                    existing_component = {
                        'component_id': component_id,
                        'component_num': component['component_num'],
                        'component_name': component['component_name'],
                        'area_id': component['area_id'],
                        'area_name': component['area_name'],
                        'assessments': [],
                    }
                    grouped.append(existing_component)
                
                existing_component['assessments'].append({
                    'assessment_id': assessment['id'],
                    'assessment_number': assessment['assessment_number'],
                    'country_id': assessment['country_id'],
                    'country_name': assessment['country_name'],
                    'region_id': assessment['region_id'],
                    'region_name': assessment['region_name'],
                    'date_of_assessment': assessment['date_of_assessment'],
                    'rating_value': component['rating_value'],
                    'rating_title': component['rating_title'],
                })
        
        # Add country assessments tracking
        country_assessments = {}
        for data in joined_data:
            country_name = data['country_name']
            if country_name not in country_assessments:
                country_assessments[country_name] = []
            country_assessments[country_name].append({
                'assessment_number': data['assessment_number'],
                'date': data['date_of_assessment'],
                'area_ratings': data.get('area_ratings'),
                'components': data['components'],
                'phase': data['phase'],
                'phase_display': data['phase_display'],
            })
        
        for country in country_assessments:
            country_assessments[country].sort(
                key=lambda a: a['date'] if a['date'] else ''
            )
        
        # Write the joined data to new files
        with open(target_dir / 'map-data.json', 'w', encoding='utf-8') as f:
            json.dump(joined_data, f, indent=2)
        
        # Write the component descriptions to a separate file
        with open(target_dir / 'component-descriptions.json', 'w', encoding='utf-8') as f:
            json.dump(component_descriptions, f, indent=2)
        
        # Save the processed data to per-assessments-processed.json
        with open(target_dir / 'per-assessments-processed.json', 'w', encoding='utf-8') as f:
            json.dump({'results': processed_assessments}, f, indent=2)
        
        # Add new dashboard data file
        with open(target_dir / 'per-dashboard-data.json', 'w', encoding='utf-8') as f:
            json.dump({
                'assessments': grouped,
                'countryAssessments': country_assessments,
            }, f, indent=2)
        
        print(f'Processed {len(processed_assessments)} records successfully')
        print('Map data and component descriptions saved in JSON format')
        print('Data processing complete. Processed data saved to per-assessments-processed.json')
        print('- per-dashboard-data.json')
        
    except Exception as error:
        print('Error processing data:')
        raise


if __name__ == '__main__':
    # Get target directory from command line arguments
    target = sys.argv[1] if len(sys.argv) > 1 else None
    process_data(target)
