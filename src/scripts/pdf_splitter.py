import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(inp_path, output_folder=None):
    """
   Split a PDF into individual pages
    
    Args:
        input_pdf_path: Path to the input PDF file
        output_folder: Folder to save individual pages (optional)
    """
    
    try:
        reader = PdfReader(inp_path)
        total_pages = len(reader.pages)

        print(f"Total pages in PDF: {total_pages}")

        # If no output folder specified, create one based on input filename
        if output_folder is None:
            base_name = os.path.splitext(os.path.basename(inp_path))[0]
            output_folder = f"{base_name}_pages"
        
        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        #Split PDF into individual pages
        for page_num in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])

            #Generate output filename
            output_filename = f"page_{page_num + 1:03d}.pdf"
            output_path = os.path.join(output_folder, output_filename)

             # Write the page to a new PDF file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            print(f"Created: {output_filename}")
        
        print(f"\nSuccessfully split PDF into {total_pages} individual pages!")
        print(f"Files saved in: {os.path.abspath(output_folder)}")
        
    except FileNotFoundError:
        print(f"Error: File '{inp_path}' not found.")
    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    #Get input PDF path from user
    input_pdf = input("Enter the path yo Ur PDF file: ").strip()

    #verify file exists and is pdf
    if not os.path.exists(input_pdf):
        print(f"Error: file '{input_pdf}' does not exist.")
        return
    if not input_pdf.lower().endswith('.pdf'):
        print("Error: Please provide a PDF file.")
        return
    
    # Ask for output folder (optional)
    output_folder = input("Enter output folder path (press Enter for default): ").strip()
    if output_folder == "":
        output_folder = None
    
    # Split the PDF
    split_pdf(input_pdf, output_folder)

if __name__ == "__main__":
    main()