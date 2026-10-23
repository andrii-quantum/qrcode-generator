# qrcode-generator

Generates QR codes that open your websites, given their DNS names.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # installs qrcode[pil]
```

## Usage

```bash
# One or more domains -> qrcodes/<domain>.png
python qrcode_generator.py example.com www.example.org

# From a file (one DNS name per line, # for comments)
python qrcode_generator.py -f domains.example.txt

# SVG, custom output dir, plain http
python qrcode_generator.py example.com --format svg -o out --scheme http

# Colors and sizing (PNG)
python qrcode_generator.py example.com --fill "#0b3d91" --background white --box-size 12 --error-correction H
```

Input is normalized: `https://Example.com/path` becomes `example.com`, and internationalized
names are converted to punycode. Invalid names are skipped with a warning, and the script then exits with code 1.
