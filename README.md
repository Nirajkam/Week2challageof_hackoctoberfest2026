# Pocket Ledger

An offline-first receipt and invoice sorter for freelancers. Add photos or PDFs, extract vendor/date/amount/category using AI, organize copies into folders, and export an editable CSV.

## ⚡ LLM Providers

Pocket Ledger now supports **multiple LLM providers** — pick the one that fits your needs:

| Provider | Models | Privacy | Cost |
|----------|--------|---------|------|
| **Ollama (Local)** | gemma3:4b, llava, moondream | 🔒 Fully offline | Free |
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4.1 | ☁️ Cloud | Pay-per-use |
| **Google Gemini** | gemini-2.0-flash, gemini-2.5-flash/pro | ☁️ Cloud | Pay-per-use |
| **Anthropic Claude** | claude-sonnet-4, claude-haiku-3.5 | ☁️ Cloud | Pay-per-use |
| **Groq** | llama-4-scout | ☁️ Cloud | Pay-per-use |

Switch providers from the sidebar — no code changes needed.

## Privacy

- **Ollama mode:** the app runs on your own computer and sends receipt content only to the Ollama service at `127.0.0.1`. No internet needed.
- **Cloud mode:** receipt images are sent to the selected provider's API. A clear warning is shown in the UI.
- Streamlit is configured to listen only on `127.0.0.1`; browser usage statistics are disabled.
- Original files are never moved or changed; organized copies and `receipts.csv` are saved in the output folder.
- Extracted values can be wrong. Review the table before using it for bookkeeping or tax reporting.

## Requirements

- Python 3.10 or newer
- For local/offline use: [Ollama](https://ollama.com/download) with a vision model
- For cloud use: an API key from one of the supported providers

## Run

### Option 1: Local with Ollama (free, private)

Install Ollama and download the model once:

```bash
ollama pull gemma3:4b
```

Then, from this project directory, set up and launch the app:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Option 2: Cloud LLM (no Ollama needed)

Set up and launch:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Select a cloud provider in the sidebar and enter your API key. You can also set API keys as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AI..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk_..."
```

## Usage

Open the local address Streamlit prints (usually `http://localhost:8501`).

1. **Choose a provider** in the sidebar (Ollama, OpenAI, Gemini, Claude, or Groq)
2. **Select a model** or enter a custom model name
3. **Add receipts** via file upload or local folder path
4. **Click "Sort receipts"** to extract and organize
5. **Review and edit** the extracted data in the table
6. **Download the CSV** for bookkeeping

## Output

By default, the app creates `sorted_receipts/` in the project directory:

```text
sorted_receipts/
├── Meals/
│   └── 2026/
│       └── Acme_Cafe_2026-02-03_12.50_USD.pdf
├── Office_Supplies/
│   └── Undated/
└── receipts.csv
```

If a generated filename already exists, a numbered suffix is added rather than overwriting it. The CSV includes vendor, date, amount, currency, category, description, original filename, and sorted file path. Correct values in the table and the saved CSV updates.

## Supported input

PDF, PNG, JPG/JPEG, WEBP, and TIFF. Text-based PDFs are read locally; image-only PDFs use the first page for vision extraction.

## Tests

```bash
python -m unittest discover -s tests
```
