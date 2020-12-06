import logging

logger = logging.get("sizebot")


async def main():
    await test()


async def test():
    logger.info("Welcome to the poopview!")


if __name__ == "__main__":
    main()
