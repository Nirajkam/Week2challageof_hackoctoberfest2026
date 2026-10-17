# Pocket Ledger UI Guide

## Updated Interface

### Sidebar - Provider Selection

```
⚡ LLM Provider
┌─────────────────────────────────────┐
│ Choose provider                     │
│ ▼ Ollama (Local)                    │
│   OpenAI                            │
│   Google Gemini                     │
│   Anthropic Claude                  │
│   Groq                              │
└─────────────────────────────────────┘

🔒 Local / Offline  (badge - green)
Free, private, runs on your machine.
Requires Ollama installed.

Model
┌─────────────────────────────────────┐
│ ▼ gemma3:4b                         │
│   llava:7b                          │
│   llava:13b                         │
│   bakllava                          │
│   moondream                         │
└─────────────────────────────────────┘

Or enter a custom model name
┌─────────────────────────────────────┐
│ e.g. my-fine-tuned-model            │
└─────────────────────────────────────┘

────────────────────────────────────────

📁 Where to save
┌─────────────────────────────────────┐
│ sorted_receipts                     │
└─────────────────────────────────────┘
Files are copied here; your originals
are left untouched.
```

### Cloud Provider Example (OpenAI Selected)

```
⚡ LLM Provider
┌─────────────────────────────────────┐
│ Choose provider                     │
│ ▼ OpenAI                            │
└─────────────────────────────────────┘

☁️ Cloud API  (badge - blue)
Powerful cloud vision models.
Requires an OpenAI API key.

Model
┌─────────────────────────────────────┐
│ ▼ gpt-4o                            │
│   gpt-4o-mini                       │
│   gpt-4.1                           │
│   gpt-4.1-mini                      │
│   o4-mini                           │
└─────────────────────────────────────┘

API Key
┌─────────────────────────────────────┐
│ ••••••••••••••••••••••              │
└─────────────────────────────────────┘
Or set the OPENAI_API_KEY
environment variable.
```

### Main Area - Privacy Indicators

**Local Mode (Ollama):**
```
ℹ️ 🔒 Private by design: files are handled by
   this local app and sent only to Ollama at
   127.0.0.1. No internet needed for receipt
   processing.
```

**Cloud Mode (any cloud provider):**
```
⚠️ ☁️ Cloud mode: receipt images will be sent
   to OpenAI's API. Do not use this with
   sensitive receipts unless you trust the
   provider.
```

### Processing Button

```
┌─────────────────────────────────────┐
│     ⚡ Sort receipts                 │
└─────────────────────────────────────┘
```

## Provider Comparison in UI

Users see this information when hovering or selecting providers:

| Provider Badge | Description |
|----------------|-------------|
| 🔒 Local / Offline | Green badge - Ollama runs on your machine |
| ☁️ Cloud API | Blue badge - External API, requires key |

## Workflow Examples

### Example 1: Complete Offline Setup (Privacy-focused)
1. Install Ollama → `ollama pull gemma3:4b`
2. Launch app → `streamlit run app.py`
3. Sidebar: Keep "Ollama (Local)" selected
4. Main: Upload receipts
5. Click "⚡ Sort receipts"
6. ✅ All processing happens locally

### Example 2: Fast Cloud Processing (OpenAI)
1. Get OpenAI API key from platform.openai.com
2. Set env var → `export OPENAI_API_KEY="sk-..."`
3. Launch app → `streamlit run app.py`
4. Sidebar: Select "OpenAI" → model "gpt-4o-mini"
5. Main: Upload receipts
6. See cloud warning ⚠️
7. Click "⚡ Sort receipts"
8. ✅ Fast results from cloud API

### Example 3: Cost-Effective (Google Gemini)
1. Get Google API key from ai.google.dev
2. Launch app → `streamlit run app.py`
3. Sidebar: Select "Google Gemini" → "gemini-2.0-flash"
4. Sidebar: Enter API key in password field
5. Main: Upload receipts
6. Click "⚡ Sort receipts"
7. ✅ Affordable cloud processing

## Visual Flow

```
User opens app
    ↓
┌───────────────────────────────────────┐
│  🧾 Pocket Ledger                     │
│  Your receipts, organized - powered   │
│  by AI. Choose local or cloud LLMs.   │
└───────────────────────────────────────┘
    ↓
Sidebar: Choose provider & model
    ↓
Main: Upload files or enter folder path
    ↓
Privacy indicator appears
    ↓
Click "⚡ Sort receipts"
    ↓
Progress bar shows processing
    ↓
Table appears with extracted data
    ↓
Edit values if needed (inline editing)
    ↓
Download CSV or view in sorted_receipts/
```

## Key UI Improvements

✅ **Provider badges** - Instant visual distinction between local/cloud  
✅ **Privacy warnings** - Clear disclosure before processing  
✅ **Custom model support** - Power users can use fine-tuned models  
✅ **Password field for keys** - Secure input (no shoulder surfing)  
✅ **Environment variable hints** - Alternative to UI input  
✅ **Gradient hero banner** - Modern, polished look  
✅ **Emoji icons** - Quick visual scanning (🔒 🧾 ⚡ ☁️ 📁 📥)
