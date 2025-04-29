"""
Example usage:
    python get_case_report_pmcids.py \
    --start-date 2015/01/01 \
    --email [email] \
    --output case_report_pmcids.csv
"""

from Bio import Entrez
import pandas as pd
import time
import argparse
from datetime import datetime

def validate_date(date_str):
    """Validate date string is in YYYY/MM/DD format"""
    try:
        datetime.strptime(date_str, '%Y/%m/%d')
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format. Use YYYY/MM/DD")

def fetch_case_report_pmcids(start_date, email, output_file):
    """Fetch PMCIDs for case reports from start date to present"""
    
    Entrez.email = email
    
    # Construct query with date range
    query = f'Case Reports[pt] AND "{start_date}"[PDAT] : "3000"[PDAT]'
    
    # First get total count
    handle = Entrez.esearch(db="pmc", term=query, retmax=0, usehistory="y")
    results = Entrez.read(handle)
    handle.close()
    
    count = int(results["Count"])
    webenv = results["WebEnv"]
    query_key = results["QueryKey"]
    
    print(f"Found {count:,} case reports in PMC from {start_date} to present")
    
    # Fetch in batches of 5000
    batch_size = 5000
    pmcids = []
    
    for start in range(0, count, batch_size):
        try:
            # Fetch this batch
            handle = Entrez.esearch(
                db="pmc",
                term=query,
                retstart=start,
                retmax=batch_size,
                webenv=webenv,
                query_key=query_key
            )
            batch_results = Entrez.read(handle)
            handle.close()
            
            # Add PMCIDs to list
            pmcids.extend(batch_results["IdList"])
            
            print(f"Processed PMCIDs {start+1:,} to {min(start+batch_size, count):,}")
            time.sleep(0.34)  # Be nice to NCBI servers
            
        except Exception as e:
            print(f"Error fetching batch starting at {start}: {e}")
            continue
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame({'pmcid': [f"PMC{pmcid}" for pmcid in pmcids]})
    df.to_csv(output_file, index=False)
    
    print(f"\nResults saved to {output_file}")
    print(f"Total PMCIDs retrieved: {len(df):,}")
    return df

def main():
    parser = argparse.ArgumentParser(description='Fetch PMCIDs for case reports from start date to present')
    
    parser.add_argument('--start-date', 
                       type=validate_date,
                       required=True,
                       help='Start date in YYYY/MM/DD format')
    
    parser.add_argument('--email',
                       type=str,
                       required=True,
                       help='Your email address (required by NCBI)')
    
    parser.add_argument('--output',
                       type=str,
                       default='case_report_pmcids.csv',
                       help='Output CSV filename (default: case_report_pmcids.csv)')
    
    args = parser.parse_args()
    
    fetch_case_report_pmcids(
        start_date=args.start_date,
        email=args.email,
        output_file=args.output
    )

if __name__ == "__main__":
    
    main()