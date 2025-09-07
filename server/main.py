import fitz
import json
from collections import Counter

def extract_headings_with_fitz(pdf_path, output_json_path):
    """Extract headings using PyMuPDF with better text reconstruction"""
    headings = []
    
    try:
        doc = fitz.open(pdf_path)
        
        # First pass: collect font sizes and identify paragraph font
        all_font_sizes = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():  # Only non-empty text
                                all_font_sizes.append(round(span["size"], 1))
        
        # Determine paragraph font size
        font_counter = Counter(all_font_sizes)
        paragraph_font_size = font_counter.most_common(1)[0][0] if font_counter else 12
        heading_threshold = paragraph_font_size + 1  # More conservative threshold
        
        print(f"Paragraph font size: {paragraph_font_size}, Heading threshold: {heading_threshold}")
        
        # Second pass: extract headings by reconstructing complete lines
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        # Reconstruct complete line text
                        line_text = ""
                        max_font_size = 0
                        font_name = ""
                        
                        for span in line["spans"]:
                            line_text += span["text"]
                            if span["size"] > max_font_size:
                                max_font_size = span["size"]
                                font_name = span["font"]
                        
                        line_text = line_text.strip()
                        
                        # Filter for potential headings
                        if (max_font_size >= heading_threshold and 
                            len(line_text) > 3 and  # Minimum length
                            len(line_text) < 200 and  # Maximum length
                            not line_text.isdigit() and  # Not just numbers
                            line_text.count(' ') < 15):  # Not too many words
                            
                            headings.append({
                                "text": line_text,
                                "page": page_num + 1,
                                "font_size": round(max_font_size, 1),
                                "font_name": font_name
                            })
        
        doc.close()
        
        # Post-process to remove duplicates and very similar entries
        filtered_headings = []
        seen_texts = set()
        
        for heading in headings:
            text_lower = heading["text"].lower().strip()
            if text_lower not in seen_texts and len(text_lower) > 3:
                seen_texts.add(text_lower)
                filtered_headings.append(heading)
        
        # Save to JSON
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump({
                "extraction_method": "PyMuPDF (fitz)",
                "paragraph_font_size": paragraph_font_size,
                "heading_threshold": heading_threshold,
                "total_headings": len(filtered_headings),
                "headings": filtered_headings
            }, json_file, indent=2, ensure_ascii=False)
        
        print(f"PyMuPDF: Extracted {len(filtered_headings)} headings")
        return filtered_headings
        
    except Exception as e:
        print(f"PyMuPDF Error: {str(e)}")
        return []


from unstructured.partition.pdf import partition_pdf
import json

def extract_headings_with_unstructured(pdf_path, output_json_path):
    """Extract headings using unstructured library"""
    
    try:
        # Partition the PDF - this automatically detects document structure
        elements = partition_pdf(
            pdf_path,
            strategy="hi_res",  # High resolution for better detection
            infer_table_structure=True
        )
        
        headings = []
        for i, element in enumerate(elements):
            # Check if element is a title, header, or heading
            if element.category in ["Title", "Header", "NarrativeText"]:
                text = str(element).strip()
                
                # Filter for likely headings
                if (len(text) > 3 and 
                    len(text) < 200 and
                    text.count('\n') == 0 and  # Single line
                    not text.isdigit()):
                    
                    # Try to get page number from metadata
                    page_num = 1
                    if hasattr(element, 'metadata') and hasattr(element.metadata, 'page_number'):
                        page_num = element.metadata.page_number
                    
                    headings.append({
                        "text": text,
                        "page": page_num,
                        "category": element.category,
                        "element_id": i
                    })
        
        # Remove duplicates
        unique_headings = []
        seen_texts = set()
        
        for heading in headings:
            text_lower = heading["text"].lower().strip()
            if text_lower not in seen_texts:
                seen_texts.add(text_lower)
                unique_headings.append(heading)
        
        # Save to JSON
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump({
                "extraction_method": "Unstructured",
                "total_headings": len(unique_headings),
                "headings": unique_headings
            }, json_file, indent=2, ensure_ascii=False)
        
        print(f"Unstructured: Extracted {len(unique_headings)} headings")
        return unique_headings
        
    except Exception as e:
        print(f"Unstructured Error: {str(e)}")
        return []


from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
import json
from collections import Counter, defaultdict

def extract_headings_with_pdfminer(pdf_path, output_json_path):
    """Extract headings using pdfminer.six with line reconstruction"""
    
    headings = []
    all_font_sizes = []
    
    try:
        # First pass: collect all font sizes
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for text_line in element:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                all_font_sizes.append(round(character.height, 1))
        
        # Determine paragraph font size
        font_counter = Counter(all_font_sizes)
        paragraph_font_size = font_counter.most_common(1)[0][0] if font_counter else 12
        heading_threshold = paragraph_font_size + 1
        
        print(f"PDFMiner - Paragraph font: {paragraph_font_size}, Threshold: {heading_threshold}")
        
        # Second pass: extract headings with line reconstruction
        for page_num, page_layout in enumerate(extract_pages(pdf_path), 1):
            # Group text elements by approximate y-coordinate to reconstruct lines
            lines_by_y = defaultdict(list)
            
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    y_coord = round(element.y1, 0)  # Round to nearest pixel
                    max_font_size = 0
                    text = element.get_text().strip()
                    
                    # Get maximum font size in this text container
                    for text_line in element:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                max_font_size = max(max_font_size, character.height)
                    
                    if text and max_font_size > 0:
                        lines_by_y[y_coord].append({
                            'text': text,
                            'font_size': max_font_size,
                            'x': element.x0
                        })
            
            # Process each line
            for y_coord, line_elements in lines_by_y.items():
                # Sort by x-coordinate and combine text
                line_elements.sort(key=lambda x: x['x'])
                combined_text = ' '.join([elem['text'] for elem in line_elements]).strip()
                max_font_size = max([elem['font_size'] for elem in line_elements])
                
                # Check if this line is a heading
                if (max_font_size >= heading_threshold and 
                    len(combined_text) > 3 and 
                    len(combined_text) < 200 and
                    combined_text.count('\n') == 0 and
                    not combined_text.isdigit()):
                    
                    headings.append({
                        "text": combined_text,
                        "page": page_num,
                        "font_size": round(max_font_size, 1)
                    })
        
        # Remove duplicates
        unique_headings = []
        seen_texts = set()
        
        for heading in headings:
            text_lower = heading["text"].lower().strip()
            if text_lower not in seen_texts:
                seen_texts.add(text_lower)
                unique_headings.append(heading)
        
        # Save to JSON
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump({
                "extraction_method": "PDFMiner.six",
                "paragraph_font_size": paragraph_font_size,
                "heading_threshold": heading_threshold,
                "total_headings": len(unique_headings),
                "headings": unique_headings
            }, json_file, indent=2, ensure_ascii=False)
        
        print(f"PDFMiner: Extracted {len(unique_headings)} headings")
        return unique_headings
        
    except Exception as e:
        print(f"PDFMiner Error: {str(e)}")
        return []


def main():
    pdf_file = "./doc/book2.pdf"  # Your PDF path
    
    print("Extracting headings using multiple methods...")
    print("=" * 50)
    
    # Method 1: PyMuPDF (fitz) - Usually the best
    # headings_fitz = extract_headings_with_fitz(pdf_file, "headings_fitz.json")
    
    # Method 2: Unstructured - Good for automatic structure detection
    headings_unstructured = extract_headings_with_unstructured(pdf_file, "headings_unstructured.json")
    
    # Method 3: PDFMiner - Alternative font-based approach
    # headings_pdfminer = extract_headings_with_pdfminer(pdf_file, "headings_pdfminer.json")
    
    # Method 4: OCR - Only use if PDF is scanned/image-based
    # headings_ocr = extract_headings_from_scanned_pdf(pdf_file, "headings_ocr.json")
    
    print("=" * 50)
    print("Summary:")
    # print(f"PyMuPDF (fitz): {len(headings_fitz)} headings")
    print(f"Unstructured: {len(headings_unstructured)} headings")  
    # print(f"PDFMiner: {len(headings_pdfminer)} headings")
    
    # Show sample results from best method (PyMuPDF)
    # if headings_fitz:
    #     print(f"\nSample headings from PyMuPDF:")
    #     for heading in headings_fitz[:10]:
    #         print(f"Page {heading['page']}: {heading['text'][:60]}...")

if __name__ == "__main__":
    main()


