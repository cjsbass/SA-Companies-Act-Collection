#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Get current timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")

# Function to monitor a process
monitor_process() {
    local pid=$1
    local name=$2
    local log_file=$3
    
    while kill -0 $pid 2>/dev/null; do
        echo "$(date): $name is still running (PID: $pid)"
        echo "Last few log entries:"
        tail -n 5 "$log_file"
        sleep 60
    done
    
    echo "$(date): $name has finished"
}

# Start core legislation downloader
echo "Starting core legislation downloader..."
nohup python3 core_legislation_downloader.py > logs/core_legislation_${timestamp}.log 2>&1 &
core_pid=$!
echo "Core legislation downloader started with PID: $core_pid"

# Start regulatory materials scraper
echo "Starting regulatory materials scraper..."
nohup python3 regulatory_materials_scraper.py > logs/regulatory_materials_${timestamp}.log 2>&1 &
regulatory_pid=$!
echo "Regulatory materials scraper started with PID: $regulatory_pid"

# Start historical case law scraper
echo "Starting historical case law scraper..."
nohup python3 historical_caselaw_scraper.py > logs/historical_caselaw_${timestamp}.log 2>&1 &
caselaw_pid=$!
echo "Historical case law scraper started with PID: $caselaw_pid"

# Monitor all processes in parallel
monitor_process $core_pid "Core legislation downloader" "logs/core_legislation_${timestamp}.log" &
monitor_process $regulatory_pid "Regulatory materials scraper" "logs/regulatory_materials_${timestamp}.log" &
monitor_process $caselaw_pid "Historical case law scraper" "logs/historical_caselaw_${timestamp}.log" &

# Wait for all monitoring processes to finish
wait

echo "All scrapers have completed!"

# Create summary of downloaded files
echo "Creating summary of downloaded files..."
echo "=== Download Summary ($(date)) ===" > download_summary.txt
echo "" >> download_summary.txt

echo "Core Legislation:" >> download_summary.txt
find core_legislation -type f | wc -l >> download_summary.txt
echo "Files by category:" >> download_summary.txt
for dir in core_legislation/*/; do
    echo "$(basename $dir): $(find $dir -type f | wc -l)" >> download_summary.txt
done
echo "" >> download_summary.txt

echo "Regulatory Materials:" >> download_summary.txt
find regulatory_materials -type f | wc -l >> download_summary.txt
echo "Files by regulator:" >> download_summary.txt
for dir in regulatory_materials/*/; do
    echo "$(basename $dir): $(find $dir -type f | wc -l)" >> download_summary.txt
done
echo "" >> download_summary.txt

echo "Historical Case Law:" >> download_summary.txt
find historical_caselaw -type f | wc -l >> download_summary.txt
echo "Files by court:" >> download_summary.txt
for dir in historical_caselaw/*/; do
    echo "$(basename $dir): $(find $dir -type f | wc -l)" >> download_summary.txt
done

echo "Summary has been saved to download_summary.txt" 