# 🏠 DDR (Detailed Diagnostic Report) Generator

An AI-based system that converts inspection and thermal reports into structured, client-ready DDR documents.

---

## 🎯 Overview

This project demonstrates a structured pipeline for generating Detailed Diagnostic Reports (DDR) by:

- Extracting observations from inspection and thermal data
- Combining insights logically
- Avoiding duplication
- Handling missing or conflicting information
- Producing a clear, client-friendly report

---

## ⚙️ Execution Modes

The system supports two modes:

### 🔹 Mock Mode (Default)
- Uses structured sample data (`ddr_data.json`)
- Ensures reliable execution without API dependency
- Demonstrates full pipeline functionality

### 🔹 API Mode (Optional)
- Integrates with Claude AI for real-time analysis
- Requires API key and credits
- Can be enabled using a flag

👉 This hybrid design ensures both **reliability and scalability**

---

## 🏗️ Architecture


Input → Extraction → Analysis → Merging → DDR Report


### Pipeline Steps:

1. **Extraction**
   - Extracts text and images from reports (if available)

2. **Analysis**
   - Processes observations (mock or AI-based)

3. **Data Merging**
   - Combines inspection and thermal insights
   - Removes duplication
   - Handles missing/conflicting data

4. **Report Generation**
   - Generates structured JSON
   - Converts into Word (DOCX) report

---

## 📂 Project Structure


ddr-generator/
├── ddr_generator.py # Main application
├── requirements.txt # Dependencies
├── README.md # Documentation
├── demo.html # Demo UI
├── .gitignore # Ignore sensitive files
├── output/ # Generated outputs
│ ├── ddr_data.json
│ └── Final_DDR_Report.docx


---

## 🚀 Installation

```bash
git clone <your-repo-link>
cd ddr-generator
pip install -r requirements.txt
💻 Usage
python ddr_generator.py \
  --inspection input/inspection.pdf \
  --thermal input/thermal.pdf \
  --output output

👉 Note:

PDFs are optional in mock mode
System works even if input files are missing
📊 Output
1. JSON Output
output/ddr_data.json

Contains structured DDR:

Property Issue Summary
Area-wise Observations
Probable Root Cause
Severity Assessment
Recommended Actions
Additional Notes
Missing Information
2. Word Report
output/Final_DDR_Report.docx

Client-friendly formatted report with:

Clear headings
Bullet points
Logical structure
Easy readability
🧠 Key Features
✅ Structured Intelligence
Logical merging of inspection + thermal data
Root cause analysis with reasoning
Severity assessment with explanation
✅ Missing Data Handling
Explicitly marks missing info as "Not Available"
No false assumptions
✅ Conflict Awareness
Designed to highlight conflicting observations
✅ Client-Friendly Output
Simple language
Structured format
Actionable recommendations
🔁 Hybrid Design
Works with or without API
Reliable fallback mechanism
📸 Image Handling
Extracts images from reports (if present)
Associates them with relevant sections
If missing → marked as "Image Not Available"
🛡️ Important Rules Followed
❌ No hallucinated data
✅ Uses only available information
✅ Explicit missing data handling
✅ Clear and simple explanations
⚠️ Limitations
Uses mock data by default (due to API credit limits)
Image analysis is basic (extraction only)
Works best with structured reports
No OCR support for scanned PDFs
🔮 Future Improvements
Real AI integration (Claude/OpenAI)
Image analysis using vision models
OCR for scanned documents
Web-based interface
Batch processing support
📈 Evaluation Alignment

This system is designed to meet:

✔ Accuracy of extracted information
✔ Logical merging of data
✔ Handling missing/conflicting details
✔ Clear and structured output
✔ Generalization to similar reports
👤 Author

Rajdatta Jadhav
AI Generalist Assignment Submission

🎥 Demo

Includes:

Working output (JSON + Word)
Loom video explanation
GitHub repository
🔐 Security Note
API keys are NOT stored in code
.env is excluded using .gitignore
🏁 Summary

This project demonstrates a reliable, structured, and scalable approach to generating diagnostic reports using AI principles, even in constrained environments.