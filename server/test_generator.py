import asyncio
from app.services.generator import generator_service

async def test_generator():
    print("Starting generator test...")
    stream = generator_service.generate_stream("查询北京今天的天气，包含温度、湿度、风速等信息")
    with open('test_output.jsonl', 'w', encoding='utf-8') as f:
        try:
            async for chunk in stream:
                f.write(chunk)
                print(f"Wrote chunk of length {len(chunk)}")
        except Exception as e:
            f.write(f"ERROR: {e}\\n")
            print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test_generator())
