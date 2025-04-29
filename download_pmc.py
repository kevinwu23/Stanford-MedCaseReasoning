import os
import ftplib
import requests
from datetime import datetime
import gzip
import shutil
import csv
from pathlib import Path
import re

def download_pmc_bulk_xml():
    """
    Downloads PMC Open Access bulk XML files and their filelists for commercial and 
    non-commercial licenses from 2024 onwards.
    """
    # Create base directories
    base_dir = Path("pmc_bulk_downloads")
    base_dir.mkdir(exist_ok=True)
    
    # FTP connection details
    ftp_host = "ftp.ncbi.nlm.nih.gov"
    base_path = "/pub/pmc/oa_bulk"
    
    # Categories to download
    categories = ["oa_comm", "oa_noncomm"]
    
    try:
        # Connect to FTP
        ftp = ftplib.FTP(ftp_host)
        ftp.login()
        
        for category in categories:
            print(f"\nProcessing {category}...")
            category_dir = base_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Navigate to XML directory
            ftp_category_path = f"{base_path}/{category}/xml"
            ftp.cwd(ftp_category_path)
            
            # List all files
            files = ftp.nlst()
            
            # Filter for baseline, incremental files, and their filelists from 2024
            target_files = []
            
            # Add baseline files and their filelists
            baseline_pattern = re.compile(r'.*baseline\.2024.*\.(tar\.gz|filelist\.csv|filelist\.txt)$')
            baseline_files = [f for f in files if baseline_pattern.match(f)]
            target_files.extend(baseline_files)
            
            # Add incremental files and their filelists
            incr_pattern = re.compile(r'.*incr\.202[45].*\.(tar\.gz|filelist\.csv|filelist\.txt)$')
            incr_files = [f for f in files if incr_pattern.match(f)]
            target_files.extend(incr_files)
            
            print(f"Found {len(target_files)} files to download in {category}")
            
            for file in target_files:
                target_file = category_dir / file
                
                # Skip if file already exists and has size > 0
                if target_file.exists() and target_file.stat().st_size > 0:
                    print(f"Skipping {file} - already downloaded")
                    continue
                
                print(f"Downloading {file}...")
                
                # Download file
                with open(target_file, 'wb') as fp:
                    ftp.retrbinary(f'RETR {file}', fp.write)
                
                print(f"Successfully downloaded {file}")
                
        ftp.quit()
        print("\nDownload completed successfully!")
        
    except ftplib.all_errors as e:
        print(f"FTP error occurred: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    download_pmc_bulk_xml()