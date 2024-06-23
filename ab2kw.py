# This script extracts keywords from a csv file containing arXiv papers using the Azure OpenAI API. It reads the papers from the input CSV file, processes each paper to extract keywords, and writes the keywords to an output CSV file.
# In practice, this code extracts keywords of papers from the hep-th category on arXiv in the last year. 

import csv
from openai import AzureOpenAI

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key="your_api_key_here",
    api_version="2024-02-01",
    azure_endpoint="https://your_azure_endpoint_here"
)

input_filename = 'arxiv_papers_10k.csv'
output_filename = 'keywords_output_10k.csv'

# Step 1: Read papers from the input CSV file
papers = []
with open(input_filename, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        papers.append({
            'index': row['Index'],
            'arxiv_id': row['arXiv ID'],
            'title': row['Title'],
            'abstract': row['Abstract']
        })

print(f"Successfully read {len(papers)} papers from {input_filename}.")

# Counter for processed papers
processed_count = 0
total_papers = len(papers)
total_tokens_used = 0

# Prepare to write the output file
with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Index', 'arXiv ID', 'Keywords'])

    # Step 2: Process each paper to extract keywords
    for paper in papers:
        paper_text = paper['abstract']
        messages = [
            {"role": "system", "content": "You are an AI assistant that helps people review and summarize physics research. Messages will contain the text of a journal article and you will respond with the top 10 key terms of the text."},
            {"role": "user", "content": "<paper text>"},
            {"role": "assistant", "content": "Key terms:\n\n1. <key term 1>\n2. <key term 2>\n3. <key term 3>\n4. <key term 4>\n5. <key term 5>\n6. <key term 6>\n7. <key term 7>\n8. <key term 8>\n9. <key term 9>\n10.<key term 10>\n\n"},
            {"role": "user", "content": paper_text}
        ]

        model_used = "gpt-35-turbo"
        T = 1.0

        try:
            response = client.chat.completions.create(
                model=model_used,
                messages=messages,
                max_tokens=500,
                temperature=T
            )
            
            key_terms_response = response.choices[0].message.content
            print(f"\nProcessing paper {processed_count + 1}/{total_papers}: {paper['title']} (arXiv ID: {paper['arxiv_id']})")
            print(key_terms_response)

            usage = response.usage
            print("\nUsage Details:")
            print(f"Prompt Tokens: {usage.prompt_tokens}")
            print(f"Completion Tokens: {usage.completion_tokens}")
            print(f"Total Tokens: {usage.total_tokens}")

            total_tokens_used += usage.total_tokens

            # Extract keywords from the response
            key_terms = [line.split('. ')[1] for line in key_terms_response.split('\n') if line.strip() and line[0].isdigit()]

            # Write the paper's keywords to the output CSV
            writer.writerow([paper['index'], paper['arxiv_id'], ', '.join(key_terms)])

            processed_count += 1

        except Exception as e:
            print(f"Error processing paper {paper['arxiv_id']}: {e}")
            writer.writerow([paper['index'], paper['arxiv_id'], "Error extracting keywords"])

print(f"\nProcessing complete. Total papers processed: {processed_count} of {total_papers}.")
print(f"Total tokens used in processing: {total_tokens_used}")
