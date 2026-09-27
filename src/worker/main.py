import asyncio


async def main() -> None:
    # Phase 0 placeholder; Phase 1 implements the PostgreSQL-backed job loop.
    while True:
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
