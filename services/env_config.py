from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..",".env"))

class EnvConfig:

  DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() in (
    "true",
    "1",
    "t",
  )
  PUBLIC_TESTNET_API_KEY = os.getenv("PUBLIC_TEST_API")
  PRIVATE_TESTNET_API_KEY = os.getenv("PRIVATE_TEST_API")



