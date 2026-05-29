import asyncio
import json
import httpx

INPUT_FILE = "research/dota_info/gsi/8654087914_gsi.jsonl"
OUTPUT_FILE = "output.jsonl"
API_URL = "http://localhost:8000/gsi-input"  # замени на свой URL

async def process_line(client: httpx.AsyncClient, line: str):
    data = json.loads(line)
    try:
        response = await client.post(API_URL, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "input": data}

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
             open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

            for line in infile:
                line = line.strip()
                if not line:
                    continue
                result = await process_line(client, line)
                outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    asyncio.run(main())