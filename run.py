import sys
import os

# Добавляем корневую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.main import PriceTrackerBot

if __name__ == '__main__':
    bot = PriceTrackerBot()
    bot.run()