import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    def __init__(self, env_file: Optional[Path] = None):
        if env_file is None:
            root = Path(__file__).resolve().parent.parent
            env_file = root / '.env'
        
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
        
        self._load_config()
    
    def _load_config(self):
        self.database_url = os.getenv('SQLALCHEMY_DATABASE_URL')
        if not self.database_url:
            raise RuntimeError("SQLALCHEMY_DATABASE_URL is not set in environment")
        
        self.redis_url = os.getenv("REDIS_URL")
        if not self.redis_url:
            raise RuntimeError("REDIS_URL is not set in environment")
        
        batch_size_env = os.getenv("BATCH_SIZE")
        if batch_size_env is None:
            raise RuntimeError("BATCH_SIZE is not set in environment")
        
        try:
            self.batch_size = int(batch_size_env)
            if self.batch_size <= 0:
                raise ValueError("BATCH_SIZE must be a positive integer")
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Invalid BATCH_SIZE in environment: {e}")
        
        self.csv_deletion_policy = os.getenv("CSV_DELETION_POLICY", "always").lower()
        if self.csv_deletion_policy not in ["always", "success", "never"]:
            raise RuntimeError(
                f"Invalid CSV_DELETION_POLICY: {self.csv_deletion_policy}. "
                "Must be 'always', 'success', or 'never'"
            )
        
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))


_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
