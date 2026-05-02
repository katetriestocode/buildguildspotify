import re
import os

files = ["framebg.c","frameidle.c","framestudy.c","frametired.c"] 

for c_file in files:
    if not os.path.exists(c_file):
        continue
        
    with open(c_file, "r") as f:
        content = f.read()
        # Find all hex values (e.g., 0xdd)
        hex_values = re.findall(r'0x[0-9a-fA-F]{2}', content)
        # Convert hex strings to actual bytes
        byte_data = bytes([int(x, 16) for x in hex_values])
        
        # Save as a .bin file
        bin_name = c_file.replace(".c", ".bin")
        with open(bin_name, "wb") as bf:
            bf.write(byte_data)
        print(f"Created {bin_name}")
