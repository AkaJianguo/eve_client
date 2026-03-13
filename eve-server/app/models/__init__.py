# app/models/__init__.py

# 1. 把空白签到本放在前台
from .base import Base

# 2. 强制所有员工来前台签到
from .user import User, Character
from .operations import CharacterAsset, CharacterWalletBalance, CharacterWalletJournalEntry, CharacterWalletTransaction
from .market import MarketHistory
from .sde import SdeMarketGroup, SdeType
from .universe import UniverseName

# 以后有了新表（比如 industry.py），只需要在这里加一行：
# from .industry import IndustryJob