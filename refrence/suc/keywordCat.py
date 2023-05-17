import csv
import openai
import yaml
import time
from threading import Thread

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

# completion_with_backoff(model="text-davinci-003", prompt="Once upon a time,")

# Set up OpenAI API credentials
openai.api_key = "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"
model_engine = "gpt-3.5-turbo"

# Set up other variables
input_file = "testSource.csv"
output_file = "output3.csv"
batch_size = 20
column_index = 0  # index of the column to use for input

# Read the source CSV file and load its contents into memory
with open(input_file, 'r') as f:
    reader = csv.DictReader(f)
    data = [row for row in reader]

# Break the input data into batches
# batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]


def generate_n_items(data, n):
    count = 0
    batch = []
    for item in data:
        batch.append(item['Keyword'])
        count += 1

        if count % n == 0:
            yield batch
            batch = []

    # Yield the remaining items in the batch, if any
    if batch:
        yield batch

# for batch in generate_n_items(data, batch_size):
#     for keyword in batch:
#         print(keyword)


# prompt engineering
# Set the system prompt message
assistantMessage1 = """You analyze SEO keywords to assign a subject and a content category. The "subject" property is the core thing a keyword is about. You will define this.  The "content category" property must be one of the following:
Company Name / Navigational
Checklists
Examples / Templates
How-to / Tutorial / Guide
Reference / Glossaries
Resource Lists / Reviews
Case Studies
Comparisons
Contests
Directory
eBooks
Games
Infographics
Integrations Page
Interviews
Live Streaming
Memes
Microsites
News
Polls
Press Releases
Product Demos
Quizzes
Research Reports
Sales Pages
Social Media Posts
Surveys
Unknown
Webinars
White Papers
Videos"""
assistantMessage2 = """The only valid output is a yaml document that has the same keys and structures as the below yaml template:

---
Keywords: # list as many keywords as provided by user
  - Keyword: {keyword_1} #provided by user
  Subject: "" #to be filled out
  ContentCategory: "" #to be filled out
  - Keyword: {keyword_2} #provided by user
  Subject: "" #to be filled out
  ContentCategory: "" #to be filled out
..."""
assistantMessage3 = """Here are several examples in yaml format
---
Keywords:
  - Keyword: iso9000 checklist
    Subject: ISO 9000
    ContentCategory: Checklists
  - Keyword: hide the timesheets worksheet
    Subject: Timesheets
    ContentCategory: How-to / Tutorial / Guide
  - Keyword: linkedin ad campaign types
    Subject: LinkedIn Ads
    ContentCategory: How-to / Tutorial / Guide
  - Keyword: integrated warehouse management system
    Subject: Warehouse Management
    ContentCategory: Resource Lists / Reviews
  - Keyword: define dearly
    Subject: Dearly
    ContentCategory: Reference / Glossaries
  - Keyword: two way sync slack
    Subject: Slack
    ContentCategory: Integrations Page
  - Keyword: developing for android on android
    Subject: Android App Development
    ContentCategory: How-to / Tutorial / Guide
  - Keyword: project management startup
    Subject: Project Management
    ContentCategory: How-to / Tutorial / Guide
  - Keyword: food poster
    Subject: Food Poster
    ContentCategory: Examples / Templates
  - Keyword: design your own thank you cards
    Subject: Thank You Cards
    ContentCategory: Resource Lists / Reviews
    - Keyword: change lewin
    Subject: Lewin's Change Management Model
    ContentCategory: Reference / Glossaries
  - Keyword: how to delete queue on spotify
    Subject: Spotify
    ContentCategory: How-to / Tutorial / Guide
  - Keyword: index of email leads
    Subject: Email Leads
    ContentCategory: Resource Lists / Reviews
  - Keyword: best free gantt chart online
    Subject: Gantt Chart
    ContentCategory: Resource Lists / Reviews
  - Keyword: date part redshift
    Subject: Redshift
    ContentCategory: Reference / Glossaries
  - Keyword: real estate open house scripts
    Subject: Real Estate Open House
    ContentCategory: How-to / Tutorial / Guide
  - Keyword: hris login
    Subject: HRIS
    ContentCategory: Company Name / Navigational
  - Keyword: free christmas photo card maker
    Subject: Christmas Card Maker
    ContentCategory: Resource Lists / Reviews
  - Keyword: free quiz website
    Subject: Quiz Maker
    ContentCategory: Resource Lists / Reviews
  - Keyword: etsy vs shopify vs amazon
    Subject: Ecommerce Platforms
    ContentCategory: Comparisons
..."""
assistantMessage4 = """What keyword may I analyze?"""
assistantMessage5 = """List as many keywords as provided by the user.
Remove all comments preceded by the number sign (#)
Use no greeting or header
Precede the YAML with three hyphens (---) on their own line
Conclude the YAML with three periods (...) on their own line
Output YAML only with all values enclosed in double quotes
For each keyword fill out each Subject and ContentCategory"""

# Iterate over the batches and send them to the ChatGPT API
merged_dicts = []

max_retries = 3
retry_delay = 5  # Delay in seconds between retries


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)


def getResult(batch):
    # Format the batch data into a format that the ChatGPT API can consume
    prompt = '\n'.join(batch)

    attempt = 1
    while attempt <= max_retries:
        try:
            response = completion_with_backoff(
                model=model_engine,
                messages=[
                    {"role": "assistant",
                        "content": assistantMessage1},
                    {"role": "assistant",
                     "content": assistantMessage2},
                    {"role": "assistant",
                     "content": assistantMessage3},
                    {"role": "assistant",
                     "content": assistantMessage4},
                    {"role": "user",
                     "content": prompt},
                    {"role": "assistant",
                     "content": assistantMessage5},
                ],
                max_tokens=2048
            )
            response_data = response.choices[0].message.content

            # If the response is successfully retrieved and formatted, break the loop
            break
        except Exception as error:
            print(f"Error on attempt {attempt}: {error}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                attempt += 1
            else:
                print("Max retries reached. Skipping this batch.")
                response_data = None
                break

    if response_data is not None:
        # Retrieve the response from the ChatGPT API and parse it
        print(response_data)
        try:
            responseDataYaml = yaml.safe_load(response_data)

            for item1 in data:
                for item2 in responseDataYaml['Keywords']:
                    if item1['Keyword'] == item2['Keyword']:
                        merged_item = {**item1, **item2}
                        merged_dicts.append(merged_item)
                        break
        except Exception as error:
            print(f"Error {error}")
            pass


threads = []
for batch in generate_n_items(data, batch_size):
    t = Thread(target=getResult, args=(batch,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# # Write the modified CSV data to a new file
# Assuming all dictionaries have the same keys
fieldnames = list(merged_dicts[0].keys())

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(merged_dicts)
