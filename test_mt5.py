import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
load_dotenv()

mt5.initialize()
print("MT5 version:", mt5.version())
authorized = mt5.login(int(os.getenv('MT5_LOGIN')),
                       os.getenv('MT5_PASSWORD'),
                       os.getenv('MT5_SERVER'))
print("Login:", authorized)
print("Account info:", mt5.account_info())
mt5.shutdown()