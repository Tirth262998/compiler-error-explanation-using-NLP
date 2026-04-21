"""
download_model.py
-----------------
Run this script ONCE to download and cache the model from Hugging Face.
After running it successfully, transformer_training.py will load from
the local cache even when offline.

Usage:
    python download_model.py
    python download_model.py --model t5-small
"""

import argparse
import time

def download_with_retry(model_name: str, max_retries: int = 5, retry_delay: int = 10):
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n[Attempt {attempt}/{max_retries}] Downloading tokenizer for '{model_name}'...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"[Attempt {attempt}/{max_retries}] Downloading model weights for '{model_name}'...")
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            print(f"\n✓ Model '{model_name}' downloaded and cached successfully!")
            print(f"  You can now run: python transformer_training.py")
            return True
        except Exception as e:
            print(f"\n[ERROR] Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"\n✗ All {max_retries} attempts failed.")
                print(f"  Please check your internet connection and ensure huggingface.co is reachable.")
                return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and cache a Hugging Face model")
    parser.add_argument("--model", type=str, default="Salesforce/codet5-base",
                        help="Model name or path (default: Salesforce/codet5-base)")
    parser.add_argument("--retries", type=int, default=5,
                        help="Number of retry attempts (default: 5)")
    parser.add_argument("--delay", type=int, default=10,
                        help="Seconds to wait between retries (default: 10)")
    args = parser.parse_args()

    print(f"=== Model Downloader ===")
    print(f"Model  : {args.model}")
    print(f"Retries: {args.retries}")

    success = download_with_retry(args.model, args.retries, args.delay)
    raise SystemExit(0 if success else 1)
