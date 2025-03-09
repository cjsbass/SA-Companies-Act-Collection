#!/bin/bash
# Script to run document processing tasks using Docker

# Make sure the script stops on any error
set -e

# Default values
INPUT_DIR="./scrapers_output"
OUTPUT_DIR="./processed_output"
MAX_FILES=""
SPECIFIC_FILE=""

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --input DIR        Input directory containing documents (default: ./scrapers_output)"
    echo "  -o, --output DIR       Output directory for processed data (default: ./processed_output)"
    echo "  -f, --file FILE        Process a single file"
    echo "  -l, --limit NUMBER     Limit processing to NUMBER files"
    echo "  -c, --citations        Process citations only"
    echo "  -s, --structure        Analyze document structure only"
    echo "  -x, --cross-refs       Map cross-references only"
    echo "  -h, --hierarchy        Model legal hierarchy only"
    echo "  -t, --temporal         Process temporal versioning only"
    echo "  -r, --reasoning        Extract legal reasoning patterns only"
    echo "  --help                 Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $0 --input ./my_docs --output ./processed"
    echo "  $0 --file ./my_docs/constitution.pdf"
    echo "  $0 --limit 100"
    echo "  $0 --citations --structure"
}

# Process command line arguments
ARGS=""
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -i|--input)
            INPUT_DIR="$2"
            ARGS="$ARGS --input /app/$(realpath --relative-to=$(pwd) $INPUT_DIR)"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            ARGS="$ARGS --output /app/$(realpath --relative-to=$(pwd) $OUTPUT_DIR)"
            shift 2
            ;;
        -f|--file)
            SPECIFIC_FILE="$2"
            ARGS="$ARGS --file /app/$(realpath --relative-to=$(pwd) $SPECIFIC_FILE)"
            shift 2
            ;;
        -l|--limit)
            MAX_FILES="$2"
            ARGS="$ARGS --limit $MAX_FILES"
            shift 2
            ;;
        -c|--citations)
            ARGS="$ARGS --citations"
            shift
            ;;
        -s|--structure)
            ARGS="$ARGS --structure"
            shift
            ;;
        -x|--cross-refs)
            ARGS="$ARGS --cross-refs"
            shift
            ;;
        -h|--hierarchy)
            ARGS="$ARGS --hierarchy"
            shift
            ;;
        -t|--temporal)
            ARGS="$ARGS --temporal"
            shift
            ;;
        -r|--reasoning)
            ARGS="$ARGS --reasoning"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $key"
            show_help
            exit 1
            ;;
    esac
done

# Ensure output directory exists
mkdir -p $OUTPUT_DIR

# Run the processing through Docker
echo "Running document processing with arguments: $ARGS"
docker run --rm -v "$(pwd)/scrapers_output:/app/scrapers_output" \
                -v "$(pwd)/processed_output:/app/processed_output" \
                -v "$(pwd)/models:/app/models" \
                -v "$(pwd)/scripts:/app/scripts" \
                legal-processor $ARGS

echo "Processing completed successfully!" 