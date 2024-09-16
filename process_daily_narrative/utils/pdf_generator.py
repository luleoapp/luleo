import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from PyPDF2 import PdfMerger
import io 
from googleapiclient.http import MediaIoBaseDownload
import mimetypes
from PIL import Image 
from fpdf import FPDF



def download_file(request):
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f'Download {int(status.progress() * 100)}%.')

    content = fh.getvalue()
    return content


def save_as_pdf(input_filename, content, output_filename=None):
    if not output_filename:
        output_filename = tempfile.mkstemp(suffix=".pdf")[1]

    file_type = mimetypes.guess_type(input_filename)[0]
    
    if file_type.startswith('image'):
        # Convert image to PDF
        image = Image.open(io.BytesIO(content))
        image.save(output_filename, "PDF", resolution=100.0)
    
    elif file_type == 'text/plain':
        # Convert text to PDF
        text = content.decode("utf-8")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        # Convert the content to utf-8 before writing
        pdf.multi_cell(0, 10, text.encode('latin1', 'replace').decode('latin1'))
        pdf.output(output_filename)
    
    else:
        raise ValueError("Unsupported file type")
    return output_filename


def combine_pdfs(pdf_list, output_path=None):
    """
    Combine multiple PDF files into a single PDF file.
    
    :param pdf_list: List of paths to the PDF files to be combined.
    :param output_path: Path to the output combined PDF file.
    """
    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
    merger = PdfMerger()

    for pdf in pdf_list:
        try:
            merger.append(pdf)
            print(f"Added {pdf}")
        except Exception as e:
            print(f"Error adding {pdf}: {e}")

    try:
        with open(output_path, 'wb') as f_out:
            merger.write(f_out)
        print(f"Combined PDF saved as {output_path}")
    except Exception as e:
        print(f"Error saving combined PDF: {e}")
    finally:
        merger.close()
    return output_path
