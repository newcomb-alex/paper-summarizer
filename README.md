# Overview
The PaperSummarizer tool works in two stages. In the first stage, an LLM is prompted to parse an input paper to extract the main headings and inject specific instructions for summarizing each section depending on the type of section. The result of this stage is a prompt containing a summary template that is unique to the input paper. By catering each template to the specific input paper rather than using the same generic template for each paper, the resulting paper summary will capture the key details of each section within the paper. This reduces the likelihood of missed details from generic templates. 

In the second stage, an LLM is given the paper and the newly created prompt and asked to fill in the template following the instructions for each section. Note that each section is prompted in a new session to avoid excessive workload in each session. This is especially useful for long technical papers and reports, where the context size may be large. The final output is a markdown file containing the summary of the paper, filled in using the template.

System prompts for stages one and two are provided under the prompts folder. These may be altered to the user's liking. 

Paper Summarizer also provides markdown to PDF conversion, including clean rendering of mathematical equations. Details on PDF conversion are provided at the bottom of this README. 

# File Structure
```
paper-summarizer/  
├── .env  
├── requirements.txt  
├── outputs/  
├── prompts/  
│   ├── stage_one_system.txt  
│   └── stage_two_system.txt  
├── papers/  
│   └── mypaper.pdf  
└── src/  
    ├── md_to_pdf.py  
    ├── pdf_utils.py   
    ├── stage_one.py    
    └── stage_two.py  
```

# Stage One
Stage one receives an input document in the form of a PDF and parses the main sections from the document using an LLM. The LLM is then prompted to inject specific instructions to each section depending on the type of section. For example, if the section details an author's methods/approach, specific instructions for extracting key elements of the proposed solution are explicitly stated. Therefore, each section within the template consists of unique instructions. If the user is interested in only specific details of a section, the system prompt may be altered to include these instructions (such as for a systematic literature review). 

The output of this stage is a machine-readable template in markdown with the following format for each section. The machine readable formatting allows easy parsing for stage two, where each section is prompted in independent sessions to improve the overall quality of the summary. 

```markdown
--------------------------------------  
## [SECTION: Introduction]  
<instructions>...injected instructions...</instructions>

## [SECTION: Methods]  
<instructions>...injected instructions...</instructions>  
--------------------------------------
```

The default LLM currently used is Claude Sonnet 4.6. This may be configured within stage_one.py. 

# Stage Two
Stage two receives the input PDF document and populates the template generated in stage one. This stage parses the template document and prompts an LLM independently for each template (paper) section. Using independent LLM sessions for each section preserves the overall quality of the summary, especially for long papers. This allows the LLM to focus only on specific sections at a time, rather than handling the entire context of the paper and template summary, which may result in missed details or vague wording. 

The output of stage two is a markdown file containing the summary. This may be converted into PDF through Paper Summarizer's built in PDF support (see below).

The default LLM currently used is Claude Sonnet 4.6. This may be configured within stage_two.py. 

# Setup Instructions
Install the dependencies: pip install -r requirements.txt

This project requires use of the OpenRouter API. Place the OpenRouter API key into a .env file within the project directory root folder. Use the following format: 

OPENROUTER_API_KEY=sk-or-...

## Stage One
First, execute stage one. The generated template may then be reviewed and edited as needed.

Stage one expects the path to the input PDF, the path to the output markdown file, and the path to the system prompt. This repository has a built-in system prompt already included for both stages. This may be edited as needed. 

Example: 
python src/stage_one.py papers/mypaper.pdf -o outputs/template.md -s prompts/stage_one_system.txt

## Stage Two
After template.md is verified and altered if necessary, stage two is ready to be executed.

Stage two expects the path to the input PDF, the path to the template markdown file, the path to the output summary, and the path to the system prompt. This repository has a built-in system prompt already included for both stages. This may be edited as needed.

Example: 
python src/stage_two.py papers/mypaper.pdf outputs/template.md -o outputs/summary.md -s prompts/stage_two_system.txt

# Markdown to PDF Support
Paper Summarizer supports PDF conversion so that the summary may be read on the user's prefered device, such as an e-reader. This module is highly customizable depending on the layout necessary. Currently, the module is configured to output a PDF document with a default font size of 14. Crucially, this module supports high quality rendering of mathematical equations using LaTeX. Pypandoc dependency may be pip installed through requirements.txt.

This module expects the input markdown file path and output path for the PDF. The font size parameter is optional (default 14). Note that only the following font sizes are supported: 8, 9, 10, 11, 12, 14, 17, and 20 pt. 

Convert the markdown summary to pdf by running the following command in the CLI: 

python src/md_to_pdf.py --input outputs/summary.md --output outputs/summary.pdf --font-size 18

Note:
Requires a LaTeX engine installed for rendering into PDF. TeX Live (Linux/macOS) or MiKTeX (Windows)

## Supported PDF Parameters
-i, --input : input file, default="summary.md"  
-o, --output : output file,  
-s, --font-size : font size, default=14  
-f, --font-family : font family, default="Times New Roman"  
-m, --margin : margin size, default="1in"  
--column-sep : column separation, default="20pt"  

## Kindle/E-Reader Support
The PDF can be optionally exported into a 6" kindle size for an e-reader by using the option --kindle in the CLI. For other e-reader sizes, the width and height of the PDF can be customized through the parameters --paper-width and --paper-height. The margin can be set with -m. 

Example: 
python src/md_to_pdf.py --input outputs/summary.md --output outputs/summary.pdf --paper-width 5in --paper-height 7in -m 0.25in