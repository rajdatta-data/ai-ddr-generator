import json
#!/usr/bin/env python3
"""
DDR (Detailed Diagnostic Report) Generator
Converts inspection and thermal reports into structured client-ready reports
"""
# from dotenv import load_dotenv
# load_dotenv()
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import base64
from datetime import datetime
USE_API = False   # change to True only if you want API

class DDRGenerator:
    """Main class for generating DDR reports from inspection data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the DDR Generator"""
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")
    
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF using pypdf"""
        try:
            import pypdf
            
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
            
            return "\n\n".join(text_content)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_images_from_pdf(self, pdf_path: str, output_dir: str) -> List[Dict[str, str]]:
        """Extract images from PDF and save them"""
        try:
            import pypdf
            from PIL import Image
            import io
            
            images = []
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        
                        for obj_name in xObject:
                            obj = xObject[obj_name]
                            
                            if obj['/Subtype'] == '/Image':
                                try:
                                    # Extract image data
                                    size = (obj['/Width'], obj['/Height'])
                                    data = obj.get_data()
                                    
                                    # Determine image format
                                    if obj['/ColorSpace'] == '/DeviceRGB':
                                        mode = "RGB"
                                    else:
                                        mode = "P"
                                    
                                    # Save image
                                    img_filename = f"page{page_num + 1}_{obj_name[1:]}.png"
                                    img_path = output_path / img_filename
                                    
                                    if obj['/Filter'] == '/DCTDecode':
                                        # JPEG image
                                        with open(img_path, 'wb') as img_file:
                                            img_file.write(data)
                                    else:
                                        # Other formats
                                        img = Image.frombytes(mode, size, data)
                                        img.save(img_path)
                                    
                                    images.append({
                                        'filename': img_filename,
                                        'path': str(img_path),
                                        'page': page_num + 1
                                    })
                                except Exception as e:
                                    print(f"Error extracting image {obj_name}: {e}")
            
            return images
        except Exception as e:
            print(f"Error extracting images from PDF: {e}")
            return []
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for API"""
        with open(image_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    
    def analyze_document_with_claude(self, document_text: str, document_type: str, 
                                     images: List[Dict] = None) -> Dict[str, Any]:
        """Use Claude API to extract structured information from document"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        prompt = f"""You are analyzing a {document_type} document. Extract all relevant information in a structured format.

Document Type: {document_type}

Extract the following information:
1. Property/Site Details (location, property type, etc.)
2. All Observations (area-wise findings, issues identified)
3. Technical Measurements (temperatures, readings, etc.)
4. Issues/Defects found
5. Any recommendations or notes
6. Image references or descriptions

For each observation, note:
- Area/Location
- Issue/Finding
- Severity indicators
- Any measurements
- Related image descriptions

Return the information as a structured JSON object with clear sections.
Be precise and include all details. If information is unclear or missing, note it explicitly.

Document Text:
{document_text}
"""
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # If no JSON, return structured text
                return {"raw_analysis": response_text, "type": document_type}
                
        except Exception as e:
            print(f"Error analyzing document: {e}")
            return {"error": str(e), "type": document_type}
    
    def merge_and_synthesize(self, inspection_data: Dict, thermal_data: Dict) -> Dict[str, Any]:
        """Use Claude to merge inspection and thermal data into DDR structure"""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        prompt = f"""You are creating a Detailed Diagnostic Report (DDR) by combining inspection and thermal data.

INSPECTION DATA:
{json.dumps(inspection_data, indent=2)}

THERMAL DATA:
{json.dumps(thermal_data, indent=2)}

Create a comprehensive DDR with the following structure. Return ONLY valid JSON:

{{
  "property_issue_summary": {{
    "property_details": "...",
    "primary_issues": ["...", "..."],
    "overall_summary": "..."
  }},
  "area_wise_observations": [
    {{
      "area": "...",
      "observations": ["...", "..."],
      "thermal_findings": "...",
      "measurements": {{}},
      "related_images": ["..."]
    }}
  ],
  "probable_root_cause": {{
    "primary_causes": ["...", "..."],
    "contributing_factors": ["...", "..."],
    "analysis": "..."
  }},
  "severity_assessment": {{
    "overall_severity": "Critical/High/Medium/Low",
    "reasoning": "...",
    "risk_factors": ["...", "..."],
    "urgency": "..."
  }},
  "recommended_actions": {{
    "immediate_actions": ["...", "..."],
    "short_term": ["...", "..."],
    "long_term": ["...", "..."],
    "preventive_measures": ["...", "..."]
  }},
  "additional_notes": [
    "..."
  ],
  "missing_information": [
    "..."
  ]
}}

IMPORTANT RULES:
1. DO NOT invent facts not in the documents
2. If information conflicts, mention it in additional_notes
3. If information is missing, list it in missing_information
4. Combine similar observations, avoid duplicates
5. Use client-friendly language, avoid unnecessary jargon
6. Be specific and actionable in recommendations
7. Link thermal findings to physical observations where relevant
8. If severity cannot be determined, explain why

Return ONLY the JSON object, no additional text.
"""
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Failed to generate structured DDR"}
                
        except Exception as e:
            print(f"Error merging data: {e}")
            return {"error": str(e)}
    
    def generate_ddr_report(self, ddr_data: Dict, output_path: str, images_dir: str = None):
        """Generate formatted DDR report as a document"""
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        # Set default font
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        
        # Title
        title = doc.add_heading('Detailed Diagnostic Report (DDR)', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Date
        date_para = doc.add_paragraph(f'Report Generated: {datetime.now().strftime("%B %d, %Y")}')
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # Spacing
        
        # 1. Property Issue Summary
        doc.add_heading('1. Property Issue Summary', 1)
        
        if 'property_issue_summary' in ddr_data:
            summary = ddr_data['property_issue_summary']
            
            if 'property_details' in summary:
                doc.add_paragraph(summary['property_details'])
            
            if 'primary_issues' in summary:
                doc.add_heading('Primary Issues Identified:', 2)
                for issue in summary['primary_issues']:
                    doc.add_paragraph(issue, style='List Bullet')
            
            if 'overall_summary' in summary:
                doc.add_heading('Summary:', 2)
                doc.add_paragraph(summary['overall_summary'])
        
        # 2. Area-wise Observations
        doc.add_heading('2. Area-wise Observations', 1)
        
        if 'area_wise_observations' in ddr_data:
            for area_obs in ddr_data['area_wise_observations']:
                doc.add_heading(f"Area: {area_obs.get('area', 'Unknown')}", 2)
                
                # Observations
                if 'observations' in area_obs:
                    doc.add_heading('Observations:', 3)
                    for obs in area_obs['observations']:
                        doc.add_paragraph(obs, style='List Bullet')
                
                # Thermal findings
                if 'thermal_findings' in area_obs and area_obs['thermal_findings']:
                    doc.add_heading('Thermal Findings:', 3)
                    doc.add_paragraph(area_obs['thermal_findings'])
                
                # Measurements
                if 'measurements' in area_obs and area_obs['measurements']:
                    doc.add_heading('Measurements:', 3)
                    for key, value in area_obs['measurements'].items():
                        doc.add_paragraph(f"{key}: {value}", style='List Bullet')
                
                # Images (placeholder for now)
                if 'related_images' in area_obs and area_obs['related_images']:
                    doc.add_heading('Related Images:', 3)
                    for img_ref in area_obs['related_images']:
                        doc.add_paragraph(f"[Image: {img_ref}]", style='List Bullet')
                
                doc.add_paragraph()  # Spacing
        
        # 3. Probable Root Cause
        doc.add_heading('3. Probable Root Cause', 1)
        
        if 'probable_root_cause' in ddr_data:
            root_cause = ddr_data['probable_root_cause']
            
            if 'primary_causes' in root_cause:
                doc.add_heading('Primary Causes:', 2)
                for cause in root_cause['primary_causes']:
                    doc.add_paragraph(cause, style='List Bullet')
            
            if 'contributing_factors' in root_cause:
                doc.add_heading('Contributing Factors:', 2)
                for factor in root_cause['contributing_factors']:
                    doc.add_paragraph(factor, style='List Bullet')
            
            if 'analysis' in root_cause:
                doc.add_heading('Analysis:', 2)
                doc.add_paragraph(root_cause['analysis'])
        
        # 4. Severity Assessment
        doc.add_heading('4. Severity Assessment', 1)
        
        if 'severity_assessment' in ddr_data:
            severity = ddr_data['severity_assessment']
            
            if 'overall_severity' in severity:
                severity_para = doc.add_paragraph()
                severity_para.add_run('Overall Severity: ').bold = True
                severity_run = severity_para.add_run(severity['overall_severity'])
                
                # Color code severity
                if severity['overall_severity'].lower() == 'critical':
                    severity_run.font.color.rgb = RGBColor(255, 0, 0)
                elif severity['overall_severity'].lower() == 'high':
                    severity_run.font.color.rgb = RGBColor(255, 165, 0)
                severity_run.bold = True
            
            if 'reasoning' in severity:
                doc.add_heading('Reasoning:', 2)
                doc.add_paragraph(severity['reasoning'])
            
            if 'risk_factors' in severity:
                doc.add_heading('Risk Factors:', 2)
                for risk in severity['risk_factors']:
                    doc.add_paragraph(risk, style='List Bullet')
            
            if 'urgency' in severity:
                doc.add_paragraph()
                urgency_para = doc.add_paragraph()
                urgency_para.add_run('Urgency: ').bold = True
                urgency_para.add_run(severity['urgency'])
        
        # 5. Recommended Actions
        doc.add_heading('5. Recommended Actions', 1)
        
        if 'recommended_actions' in ddr_data:
            actions = ddr_data['recommended_actions']
            
            if 'immediate_actions' in actions:
                doc.add_heading('Immediate Actions Required:', 2)
                for action in actions['immediate_actions']:
                    doc.add_paragraph(action, style='List Bullet')
            
            if 'short_term' in actions:
                doc.add_heading('Short-term Actions (1-3 months):', 2)
                for action in actions['short_term']:
                    doc.add_paragraph(action, style='List Bullet')
            
            if 'long_term' in actions:
                doc.add_heading('Long-term Actions (3+ months):', 2)
                for action in actions['long_term']:
                    doc.add_paragraph(action, style='List Bullet')
            
            if 'preventive_measures' in actions:
                doc.add_heading('Preventive Measures:', 2)
                for measure in actions['preventive_measures']:
                    doc.add_paragraph(measure, style='List Bullet')
        
        # 6. Additional Notes
        if 'additional_notes' in ddr_data and ddr_data['additional_notes']:
            doc.add_heading('6. Additional Notes', 1)
            for note in ddr_data['additional_notes']:
                doc.add_paragraph(note, style='List Bullet')
        
        # 7. Missing or Unclear Information
        if 'missing_information' in ddr_data and ddr_data['missing_information']:
            doc.add_heading('7. Missing or Unclear Information', 1)
            for missing in ddr_data['missing_information']:
                doc.add_paragraph(missing, style='List Bullet')
        
        # Save document
        # doc.save(output_path)
        import os

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        doc.save(output_path)
        print(f"DDR report generated: {output_path}")
    
    def process_reports(self, inspection_pdf: str, thermal_pdf: str, output_dir: str):
        """Main processing pipeline"""
        print("Starting DDR Generation Process...")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Extract text from PDFs
        print("\n1. Extracting text from inspection report...")
        inspection_text = self.extract_text_from_pdf(inspection_pdf)
        
        print("2. Extracting text from thermal report...")
        thermal_text = self.extract_text_from_pdf(thermal_pdf)
        
        # Step 2: Extract images
        print("\n3. Extracting images from inspection report...")
        inspection_images = self.extract_images_from_pdf(
            inspection_pdf, 
            str(output_path / "inspection_images")
        )
        
        print("4. Extracting images from thermal report...")
        thermal_images = self.extract_images_from_pdf(
            thermal_pdf,
            str(output_path / "thermal_images")
        )
        
        print(f"   - Extracted {len(inspection_images)} images from inspection report")
        print(f"   - Extracted {len(thermal_images)} images from thermal report")
        
        # Step 3: Analyze documents with Claude
        print("\n5. Analyzing inspection report with AI...")
        # inspection_data = self.analyze_document_with_claude(
        #     inspection_text, 
        #     "Inspection Report",
        #     inspection_images
        # )
        
        print("6. Analyzing thermal report with AI...")
        # thermal_data = self.analyze_document_with_claude(
        #     thermal_text,
        #     "Thermal Report", 
        #     thermal_images
        # )
        
        # Save intermediate analysis
        with open(output_path / "inspection_analysis.json", 'w') as f:
            # json.dump(inspection_data, f, indent=2)
             json.dump({}, f)
        
        with open(output_path / "thermal_analysis.json", 'w') as f:
            # json.dump(thermal_data, f, indent=2)
            json.dump({}, f)
        
        # Step 4: Merge and synthesize into DDR
        # print("\n7. Merging data and generating DDR structure...")
        # ddr_data = self.merge_and_synthesize(inspection_data, thermal_data)
        # import json, os

        # print("\n7. Merging data and generating DDR structure...")
        

        print("\n7. Merging data and generating DDR structure...")

# Path to DDR JSON
               # Step 7: Decide source (API or local JSON)
        ddr_path = os.path.join(output_path, "ddr_data.json")

        if USE_API and API_KEY:
            result = analyze_with_api("sample inspection + thermal text")

            if result:
                print("Using API-generated data")
                ddr_data = result
            else:
                print("API failed → using local JSON")
                with open(ddr_path, "r") as f:
                    ddr_data = json.load(f)
        else:
            print("Using local JSON (mock mode)")
            with open(ddr_path, "r") as f:
                ddr_data = json.load(f)

        # Save final DDR data
        with open(ddr_path, "w") as f:
            json.dump(ddr_data, f, indent=2)

        # Step 8: Generate final report
        print("\n8. Generating final DDR document...")

        self.generate_ddr_report(
            ddr_data,
            str(output_path / "Final_DDR_Report.docx"),
            str(output_path)
        )

        print("\nDDR Generation Complete!")
        print(f"Output directory: {output_path}")
        print(f"Final report: {output_path / 'Final_DDR_Report.docx'}")

        return ddr_data

def analyze_with_api(text):
    import anthropic
    client = anthropic.Anthropic(api_key=API_KEY)

    prompt = f"""
Return STRICT JSON with keys:
property_issue_summary, area_wise_observations,
probable_root_cause, severity_assessment,
recommended_actions, additional_notes, missing_information.

Text:
{text}
"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text

    
        return json.loads(raw)

    except Exception as e:
        print("API failed → fallback to mock:", e)
        return None
def main():
    """Main entry point for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate DDR from inspection reports')
    parser.add_argument('--inspection', required=True, help='Path to inspection report PDF')
    parser.add_argument('--thermal', required=True, help='Path to thermal report PDF')
    parser.add_argument('--output', default='./output', help='Output directory')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
    
    args = parser.parse_args()
    
    generator = DDRGenerator(api_key=args.api_key)
    generator.process_reports(args.inspection, args.thermal, args.output)


if __name__ == "__main__":
    main()
