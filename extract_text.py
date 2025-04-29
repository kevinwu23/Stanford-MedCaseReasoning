import os
from pathlib import Path
from tqdm import tqdm
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from bs4 import BeautifulSoup
import re
import pandas as pd

def extract_text(xml_path):
    """Extract text from XML file."""
    try:
        with open(xml_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        
        # Parse XML using BeautifulSoup
        soup = BeautifulSoup(xml_content, 'lxml-xml')
        
        # Extract PMC ID
        article_id_tags = soup.find_all('article-id')
        pmcid = None
        for tag in article_id_tags:
            if tag.get('pub-id-type') == 'pmc':
                pmcid = f"PMC{tag.get_text()}"
                break
        
        if not pmcid:
            return None
        
        # Extract and process main text
        body_tag = soup.find('body')
        if body_tag:
            main_text = body_tag.get_text(separator="\n", strip=True)
            main_text = re.sub(r'\[\s*\d+\s*\]', '', main_text)
            main_text = re.sub(r'((?:Figure|Fig\.)\s*\d+)[,]?\n', r'\1 ', main_text)
            main_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', main_text)
            main_text = re.sub(r'\n{3,}', '\n\n', main_text).strip()
            
            # Remove duplicate consecutive lines
            lines = main_text.split('\n')
            deduped_lines = []
            prev_line = None
            for line in lines:
                if line != prev_line:
                    deduped_lines.append(line)
                prev_line = line
            main_text = "\n".join(deduped_lines)
            
            return {
                'pmcid': pmcid,
                'text': main_text
            }
        
        return None
    
    except Exception as e:
        print(f"Error processing {xml_path}: {e}")
        return None

def process_batch(file_batch):
    """Process a batch of XML files."""
    results = []
    for xml_file in tqdm(file_batch, total=len(file_batch), desc="Processing files", leave=False):
        text_data = extract_text(xml_file)
        if text_data:
            results.append(text_data)
    return results

def process_xml_files():
    """Process XML files and save text to parquet."""
    input_dir = Path("extracted_case_reports")
    output_file = "case_reports_text.parquet"
    
    # Get list of all XML files
    xml_files = list(input_dir.glob('*.xml')) + list(input_dir.glob('*.nxml'))
    total_files = len(xml_files)
    print(f"Found {total_files} XML files to process")
    
    # Calculate batch size based on number of cores
    num_cores = max(1, multiprocessing.cpu_count() - 2)
    batch_size = max(1, total_files // (num_cores * 10))
    batches = [xml_files[i:i + batch_size] for i in range(0, len(xml_files), batch_size)]
    
    print(f"Processing files using {num_cores} cores in {len(batches)} batches")
    
    all_text_data = []
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        results = list(tqdm(
            executor.map(process_batch, batches),
            total=len(batches),
            desc="Processing batches"
        ))
        
        for batch_result in results:
            all_text_data.extend(batch_result)
    
    # Create DataFrame and save to parquet
    df = pd.DataFrame(all_text_data)
    df.to_parquet(output_file, index=False)
    
    print(f"\nProcessing complete:")
    print(f"- Text data saved to: {output_file}")
    print(f"Total articles processed: {len(df)}")

if __name__ == "__main__":
    process_xml_files()