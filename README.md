# PMC Case Report Processing Pipeline

This repository contains a complete pipeline for downloading and processing case reports from PubMed Central (PMC). The pipeline includes tools for identifying case reports, downloading bulk XML data, extracting relevant articles, and processing their metadata and text content.

## Pipeline Overview

1. Download bulk PMC XML files (`download_pmc.py`)
2. Fetch case report PMCIDs (`get_case_report_pmcids.py`)
3. Extract case report XML files (`process_pmc.py`)
4. Extract metadata from case reports (`extract_metadata.py`)
5. Extract and process full text (`extract_text.py`)

## Detailed Usage

### 1. Download PMC Bulk Files
First, download the bulk XML files from PMC's FTP server:

```bash
python download_pmc.py
```

This script:
- Downloads PMC Open Access bulk XML files from 2024 onwards
- Handles both commercial and non-commercial licenses
- Creates directory structure:
  ```
  pmc_bulk_downloads/
  ├── oa_comm/
  └── oa_noncomm/
  ```
- Automatically skips already downloaded files
- Downloads both tar.gz files and their corresponding filelists

### 2. Get Case Report PMCIDs
Next, identify all case reports in PMC:

```bash
python get_case_report_pmcids.py \
    --start-date 2015/01/01 \
    --email your.email@example.com \
    --output case_report_pmcids.csv
```

Parameters:
- `--start-date`: Start date in YYYY/MM/DD format
- `--email`: Your email (required by NCBI)
- `--output`: Output CSV file (default: case_report_pmcids.csv)

### 3. Process PMC Files
Extract case report XML files from the bulk downloads:

```bash
python process_pmc.py
```

This script:
- Reads PMCIDs from `case_report_pmcids.csv`
- Processes bulk tar.gz files in parallel
- Extracts only matching case report XML files
- Creates `extracted_case_reports/` directory with XML files
- Uses multiprocessing for faster extraction

### 4. Extract Metadata
Extract structured metadata from the XML files:

```bash
python extract_metadata.py
```

Extracts and saves metadata including:
- Accession ID (PMCID)
- Publication date
- Article title
- Journal name
- Article link
- Saves results to `metadata.csv`

### 5. Extract Full Text
Process and extract the full text content:

```bash
python extract_text.py
```

Features:
- Extracts main text content from XML
- Cleans and formats text:
  - Removes citation markers
  - Fixes figure references
  - Preserves paragraph structure
- Saves results to `case_reports_text.parquet`

## Directory Structure
.
├── pmc_bulk_downloads/ # Raw downloaded files
│ ├── oa_comm/
│ └── oa_noncomm/
├── case_report_pmcids.csv # List of case report PMCIDs
├── extracted_case_reports/ # Extracted XML files
├── metadata.csv # Extracted metadata
└── case_reports_text.parquet # Processed full text

## Requirements
pandas
beautifulsoup4
lxml
tqdm
biopython
