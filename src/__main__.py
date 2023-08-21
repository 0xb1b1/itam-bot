#! /usr/bin/env python3

# region Dependencies
from pathlib import Path
# endregion

# Create log folder if it doesn't exist
Path("/data/logs").mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    import bot
    bot.run()
