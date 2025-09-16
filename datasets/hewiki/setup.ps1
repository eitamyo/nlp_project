# Setup Hebrew Wikipedia corpus for nikud dataset

# 1. Define dump URL and output paths
$dumpUrl = "https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-pages-articles.xml.bz2"
$dumpFile = "hewiki-latest-pages-articles.xml.bz2"
$outputFolder = "hewiki-extracted"

# 2. Download if not already present
if (Test-Path $dumpFile) {
    Write-Host "Dump file already exists: $dumpFile"
} else {
    Write-Host "Downloading Hebrew Wikipedia dump..."
    Invoke-WebRequest -Uri $dumpUrl -OutFile $dumpFile
}

# 3. Install wikiextractor if not installed
Write-Host "Checking for wikiextractor..."
pip show wikiextractor > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing wikiextractor..."
    pip install wikiextractor
} else {
    Write-Host "wikiextractor already installed."
}

# 4. Extract if not already extracted
if (Test-Path $outputFolder) {
    Write-Host "Extraction folder already exists: $outputFolder"
} else {
    Write-Host "Extracting dump with WikiExtractor..."
    docker build . --pull --rm -f "Dockerfile" -t wikiextractor:latest
    docker run --rm -it -v "${PWD}/output:/app/output" wikiextractor:latest
    Write-Host "Extraction complete. Files are in $outputFolder"
}

pause