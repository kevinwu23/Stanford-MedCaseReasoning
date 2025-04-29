import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import xml.etree.ElementTree as ET
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from functools import partial

def extract_metadata_from_xml(xml_path):
    """Extract metadata from a single XML file."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Initialize default values
        metadata = {
            'accession_id': None,
            'publication_date': None,
            'title': None,
            'journal': None,
            'article_link': None
        }
        
        # Extract article id (PMC ID)
        article_ids = root.findall(".//article-id")
        for article_id in article_ids:
            if article_id.get('pub-id-type') == 'pmc':
                metadata['accession_id'] = f"{article_id.text}"
                metadata['article_link'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{metadata['accession_id']}/"
                break
        
        # Extract publication date
        pub_date = root.find(".//pub-date[@pub-type='epub']") or root.find(".//pub-date[@pub-type='ppub']")
        if pub_date is not None:
            year = pub_date.find('year')
            month = pub_date.find('month')
            day = pub_date.find('day')
            
            date_parts = []
            if year is not None: date_parts.append(year.text.zfill(4))
            if month is not None: date_parts.append(month.text.zfill(2))
            if day is not None: date_parts.append(day.text.zfill(2))
            
            metadata['publication_date'] = '-'.join(date_parts) if date_parts else None
        
        # Extract title
        title_elem = root.find(".//article-title")
        if title_elem is not None:
            metadata['title'] = ''.join(title_elem.itertext()).strip()
        
        # Extract journal name
        journal_elem = root.find(".//journal-title")
        if journal_elem is not None:
            metadata['journal'] = journal_elem.text.strip()
        
        return metadata
    
    except Exception as e:
        print(f"Error processing {xml_path}: {e}")
        return None

def process_batch(file_batch, total_files):
    """Process a batch of XML files and return their metadata."""
    results = []
    for xml_file in tqdm(file_batch, total=len(file_batch), desc="Processing files", leave=False):
        metadata = extract_metadata_from_xml(xml_file)
        if metadata:
            results.append(metadata)
    return results

def create_metadata_csv():
    """Create a metadata CSV file from all XML files in the extracted_case_reports directory."""
    input_dir = Path("extracted_case_reports")
    output_file = "metadata.csv"
    
    # Get list of all XML files
    xml_files = list(input_dir.glob('*.xml')) + list(input_dir.glob('*.nxml'))
    total_files = len(xml_files)
    print(f"Found {total_files} XML files to process")
    
    # Calculate batch size based on number of cores
    num_cores = max(1, multiprocessing.cpu_count() - 2)
    batch_size = max(1, total_files // (num_cores * 10))  # Create enough batches for good parallelization
    batches = [xml_files[i:i + batch_size] for i in range(0, len(xml_files), batch_size)]
    
    print(f"Processing files using {num_cores} cores in {len(batches)} batches")
    
    all_metadata = []
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        # Process batches in parallel
        process_fn = partial(process_batch, total_files=total_files)
        results = list(tqdm(
            executor.map(process_fn, batches),
            total=len(batches),
            desc="Processing batches"
        ))
        
        # Flatten results
        for batch_result in results:
            all_metadata.extend(batch_result)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(all_metadata)
    df.to_csv(output_file, index=False)
    print(f"\nMetadata extraction complete. Saved to {output_file}")
    print(f"Total articles processed: {len(df)}")
    
    # Print some basic statistics
    print("\nSummary:")
    print(f"Articles with publication dates: {df['publication_date'].notna().sum()}")
    print(f"Articles with titles: {df['title'].notna().sum()}")
    print(f"Articles with journal names: {df['journal'].notna().sum()}")
    print("\nMost common journals:")
    print(df['journal'].value_counts().head())

if __name__ == "__main__":
    create_metadata_csv()
