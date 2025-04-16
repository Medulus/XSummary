import os
import openai
import configparser
import pandas as pd
from fpdf import FPDF

# --- Step 1: Read configuration and set your OpenAI key ---
config = configparser.ConfigParser()
config.read('config.ini')

openai_api_key = config['openai']['api_key']
openai.api_key = openai_api_key

# --- Step 2: Functions to process CSV and generate newsletter ---

def compile_tweets_csv(csv_filename):
    """
    Reads the CSV file and concatenates tweets into a single string.
    """
    df = pd.read_csv(csv_filename)
    content = ""
    # Iterate over each tweet row
    for index, row in df.iterrows():
        content += f"{row['User']}: {row['Tweet']}\n"
    return content

def generate_newsletter(content):
    """
    Uses OpenAI's API to create a newsletter from the tweet content.
    The prompt instructs the model to summarize the tweets into a newsletter
    with sections like Highlights, Key Insights, and Implications.
    """
    prompt = f"""
    You are an expert in analyzing trends in the AI and robotics industry.
    Below are tweets from influential accounts in this space. Summarize these tweets 
    into a newsletter. The newsletter should be written in Markdown format and include:
    
    - A brief introduction
    - A "Highlights" section with key bullet points
    - A "Key Insights" section discussing the implications of these tweets on the industry
    - A closing summary
    
    Tweets:
    {content}
    
    Newsletter:
    """
    
    response = openai.Completion.create(
        engine="gpt-4o-mini",  # or a different model if preferred
        prompt=prompt,
        max_tokens=60,
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    newsletter_text = response.choices[0].text.strip()
    return newsletter_text

def save_pdf(text, filename="newsletter.pdf"):
    """
    Saves the given text into a PDF file.
    This basic implementation writes plain text line by line.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Split the text into lines and add them to the PDF
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, txt=line)
        
    pdf.output(filename)
    print(f"Newsletter PDF saved as {filename}.")

def main():
    # --- Step 3: Load the CSV file (you can change the filename as needed) ---
    csv_filename = input("Enter the CSV filename (e.g., tweets20230425123045.csv): ").strip()
    if not os.path.exists(csv_filename):
        print("CSV file not found! Please check your filename.")
        return

    tweet_content = compile_tweets_csv(csv_filename)
    print("Generating newsletter via OpenAI...")

    # --- Step 4: Generate Newsletter content using ChatGPT ---
    newsletter = generate_newsletter(tweet_content)
    
    # Save the newsletter as a Markdown file for record
    md_filename = "newsletter.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(newsletter)
    print(f"Newsletter content saved as {md_filename}")
    
    # --- Step 5: Convert the newsletter into a PDF ---
    save_pdf(newsletter, filename="newsletter.pdf")

if __name__ == "__main__":
    main()
# This script can be run in a terminal or command prompt.