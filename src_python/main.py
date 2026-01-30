"""
Main entry point for IFRC PER Data Fetcher (Python version).
Mirrors the functionality of index.js
"""
import sys
from pathlib import Path

from process_data import process_data
from fetch_data import fetch_data


def main(target_dir: str = None, skip_fetch: bool = True) -> None:
    """
    Main execution function.
    
    Args:
        target_dir: Directory for data files (default: ../data_python)
        skip_fetch: If True, skip fetching and only process (default: True)
    """
    if target_dir is None:
        target_dir = Path(__file__).parent.parent / 'data_python'
    else:
        target_dir = Path(target_dir)
    
    try:
        if not skip_fetch:
            fetch_data(str(target_dir))
        process_data(str(target_dir))
    except Exception as error:
        print(f'Error: {error}')
        sys.exit(1)


if __name__ == '__main__':
    # Parse command line arguments
    target = None
    do_fetch = False
    
    for arg in sys.argv[1:]:
        if arg == '--fetch':
            do_fetch = True
        else:
            target = arg
    
    main(target, skip_fetch=not do_fetch)
