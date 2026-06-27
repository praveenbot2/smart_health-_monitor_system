import pypandoc
import os

input_file = "PROJECT_DOCUMENTATION.md"
output_file = "Smart_Health_Monitor_Project_Report.docx"

print(f"Converting {input_file} to {output_file}...")
try:
    pypandoc.convert_file(
        input_file, 
        'docx', 
        outputfile=output_file
    )
    print(f"Successfully created {output_file} in {os.getcwd()}")
except Exception as e:
    print(f"Failed to convert: {e}")
