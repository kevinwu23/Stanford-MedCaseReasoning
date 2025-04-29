import os
import pandas as pd
import tarfile
from pathlib import Path
from tqdm import tqdm
import shutil
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

NUM_CORES = max(1, multiprocessing.cpu_count() - 2)  # Leave 2 cores free for system

def load_case_report_pmcids():
    """Load PMCIDs of known case reports."""
    try:
        df = pd.read_csv('case_report_pmcids.csv')
        pmcids = set(str(pmcid).replace('PMC', '') for pmcid in df['pmcid'])
        print(f"Loaded {len(pmcids)} case report PMCIDs")
        return pmcids
    except Exception as e:
        print(f"Error loading case report PMCIDs: {e}")
        return set()

def get_matching_files_from_filelist(filelist_path, case_report_pmcids):
    """Get list of files that correspond to case reports from a filelist."""
    try:
        filelist_df = pd.read_csv(filelist_path)
        filelist_df['clean_pmcid'] = filelist_df['AccessionID'].astype(str).str.replace('PMC', '')
        matching_files = filelist_df[filelist_df['clean_pmcid'].isin(case_report_pmcids)]
        return set(matching_files['Article File'].tolist())
    except Exception as e:
        print(f"Error processing filelist {filelist_path}: {e}")
        return set()

def process_tar_file(args):
    """Process a single tar file and extract case reports. Designed for parallel processing."""
    tar_path, filelist_csv, case_report_pmcids, output_dir = args
    temp_dir = output_dir / f"temp_{os.getpid()}"  # Use PID for unique temp dirs
    extracted_files = []
    
    try:
        # Get list of case report files from filelist
        matching_files = get_matching_files_from_filelist(filelist_csv, case_report_pmcids)
        
        if not matching_files:
            return []
        
        temp_dir.mkdir(exist_ok=True)
        
        # Extract only matching files from tar.gz
        with tarfile.open(tar_path, 'r:gz') as tar:
            matching_members = [m for m in tar.getmembers() 
                             if any(f in m.name for f in matching_files)]
            
            tar.extractall(temp_dir, members=matching_members)
            
            # Move extracted files to output directory
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(('.xml', '.nxml')):
                        src = Path(root) / file
                        dst = output_dir / file
                        if not dst.exists():  # Skip if already exists
                            shutil.move(str(src), str(dst))
                            extracted_files.append(str(dst))
        
        return extracted_files
    
    except Exception as e:
        print(f"Error processing {tar_path}: {e}")
        return []
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def extract_case_reports():
    """Extract only case report XML files from bulk downloads."""
    base_dir = Path("pmc_bulk_downloads")
    output_dir = Path("extracted_case_reports")
    output_dir.mkdir(exist_ok=True)
    
    # Load case report PMCIDs
    case_report_pmcids = load_case_report_pmcids()
    if not case_report_pmcids:
        print("No case report PMCIDs loaded. Exiting.")
        return
    
    # Collect all work to be done
    work_items = []
    for category in ['oa_comm', 'oa_noncomm']:
        category_dir = base_dir / category
        if not category_dir.exists():
            continue
        
        print(f"\nProcessing {category}...")
        filelist_csvs = sorted(category_dir.glob('*.filelist.csv'))
        print(f"Found {len(filelist_csvs)} filelist files")
        
        for filelist_csv in filelist_csvs:
            tar_name = filelist_csv.name.replace('.filelist.csv', '.tar.gz')
            tar_path = category_dir / tar_name
                
            if tar_path.exists():
                work_items.append((tar_path, filelist_csv, case_report_pmcids, output_dir))
    
    print(f"\nProcessing {len(work_items)} tar files using {NUM_CORES} cores...")
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
        results = list(tqdm(
            executor.map(process_tar_file, work_items),
            total=len(work_items),
            desc="Extracting case reports"
        ))
    
    # Report final count
    final_count = len(list(output_dir.glob('*.xml'))) + len(list(output_dir.glob('*.nxml')))
    print(f"\nExtraction complete. {final_count} case report XML files extracted to {output_dir}")

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Needed for Windows
    extract_case_reports()