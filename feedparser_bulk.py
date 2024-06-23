# This code uses feedparser to fetch papers from the hep-th category on arXiv and exports them to a CSV file. It also uses batch processing to fetch a large number of papers. 
# The parameters for batch processing are: maximum results per call, total results to fetch, sleep time between batches, and maximum retries for a batch. Note also the filename for the CSV file.
# In practice, we only need 8000 to get the papers from last year in the hep-th category.

import requests
import feedparser
from pylatexenc.latex2text import LatexNodes2Text
import csv
from datetime import datetime, timedelta
import time

def latex_to_plain_text(latex_text):
    try:
        # Convert LaTeX to plain text
        plain_text = LatexNodes2Text().latex_to_text(latex_text)
        return plain_text
    except Exception as e:
        print(f"Error converting LaTeX to plain text: {e}")
        return latex_text  # Fallback to returning the original LaTeX text if conversion fails

def fetch_and_export_arxiv_papers():
    # Get the current date and the date one year ago
    today = datetime.now().date()
    one_year_ago = today - timedelta(days=365)
    
    # Format dates in the required YYYYMMDD format
    start_date = one_year_ago.strftime("%Y%m%d")
    end_date = today.strftime("%Y%m%d")
    
    # Define query parameters
    query = f"search_query=cat:hep-th+AND+submittedDate:[{start_date} TO {end_date}]"
    base_url = f"http://export.arxiv.org/api/query?{query}&sortBy=submittedDate&sortOrder=descending"
    max_results_per_call = 200
    total_results = 10000
    sleep_time = 5  # in seconds
    max_retries = 10  # Maximum number of retries for a batch

    filename = "arxiv_papers_10k.csv"

    # Write the header to the CSV file
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Index', 'arXiv ID', 'Title', 'Abstract'])
    
    total_papers_fetched = 0
    current_index = 1

    # Loop to fetch papers in batches
    for start in range(0, total_results, max_results_per_call):
        retries = 0
        
        while retries < max_retries:
            url = f"{base_url}&start={start}&max_results={max_results_per_call}"
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an HTTPError for bad responses
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                retries += 1
                print(f"Retrying... ({retries}/{max_retries}) after sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time)
                continue
            
            # Parse the Atom feed using feedparser
            feed = feedparser.parse(response.content)
            
            batch_papers = []
            for entry in feed.entries:
                # Check if the primary category is 'hep-th'
                if 'hep-th' in entry.tags[0]['term']:
                    paper_data = {}
                    arxiv_id = entry.id.split('/')[-1]
                    title = entry.title
                    summary = entry.summary
                    
                    # Try to convert LaTeX to plain text, handle any errors
                    try:
                        abstract = latex_to_plain_text(title + '.' + summary)
                        paper_data['index'] = current_index
                        paper_data['arxiv_id'] = arxiv_id
                        paper_data['title'] = latex_to_plain_text(title)
                        paper_data['abstract'] = abstract
                        batch_papers.append(paper_data)
                        current_index += 1
                    except Exception as e:
                        print(f"Error processing entry with arXiv ID {arxiv_id}: {e}")
            
            if batch_papers:
                # Append the fetched batch to the CSV file
                with open(filename, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    for paper in batch_papers:
                        writer.writerow([paper['index'], paper['arxiv_id'], paper['title'], paper['abstract']])

                total_papers_fetched += len(batch_papers)
                print(f"Fetched {len(batch_papers)} papers in this batch. Total papers fetched so far: {total_papers_fetched}")
                break  # Exit the retry loop and proceed to the next batch
            
            print(f"No papers fetched in this batch. Retrying... ({retries + 1}/{max_retries})")
            retries += 1
            time.sleep(sleep_time)

        if retries == max_retries:
            print(f"Failed to fetch batch starting at {start} after {max_retries} retries.")
        
        print(f"Completed batch starting at {start}. Sleeping for {sleep_time} seconds before the next batch...")
        time.sleep(sleep_time)  # Wait before fetching the next batch

    print(f"Total number of papers fetched: {total_papers_fetched}")

# Fetch and export papers to CSV
fetch_and_export_arxiv_papers()
