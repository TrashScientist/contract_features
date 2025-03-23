import argparse
import uvicorn
from scripts.process_csv import process_csv_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contract Feature Engineering")
    parser.add_argument("--input", default="data.csv", help="Input CSV file path")
    parser.add_argument("--output", default="contract_features.csv", help="Output CSV file path")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    
    args = parser.parse_args()
    
    if args.serve:
        # Start the FastAPI server
        print(f"Starting FastAPI server on {args.host}:{args.port}...")
        uvicorn.run("app.main:app", host=args.host, port=args.port)
    else:
        # Process the CSV file
        print("Processing CSV file...")
        process_csv_file(args.input, args.output)