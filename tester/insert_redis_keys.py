#!/usr/bin/env python3
import redis
import ssl
import socket
import sys
from datetime import datetime

# CONFIG
REDIS_HOST = "x.x.x.x"  #Your NLB IP
REDIS_PORT = 6379

# Custom SSL Connection with SNI support
class SNISSLConnection(redis.Connection):
    def __init__(self, sni_hostname=None, **kwargs):
        self.sni_hostname = sni_hostname
        super().__init__(**kwargs)
    
    def _connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        self._sock = context.wrap_socket(sock, server_hostname=self.sni_hostname)
        return self._sock
    
    def disconnect(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except:
                pass
        self._sock = None

def connect_to_redis(env_id):
    sni_hostname = f"redis-{env_id}.redis.local"
    pool = redis.ConnectionPool(
        connection_class=SNISSLConnection,
        host=REDIS_HOST,
        port=REDIS_PORT,
        sni_hostname=sni_hostname
    )
    return redis.Redis(connection_pool=pool), sni_hostname

def main():
    # Get environment from command line or default to env1
    env_id = sys.argv[1] if len(sys.argv) > 1 else "env1"
    
    print(f"Redis Insert Tester - Environment: {env_id}")
    print("="*50)
    
    try:
        # Connect to Redis
        r, sni = connect_to_redis(env_id)
        r.ping()
        print(f"✓ Connected to {sni}")
        
        # Insert test data with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\nInserting data at {timestamp}...")
        
        # Insert various types of data
        data_to_insert = {
            f"{env_id}:string:example": f"Hello from {env_id} at {timestamp}",
            f"{env_id}:number:counter": "42",
            f"{env_id}:json:user": '{"name": "John Doe", "env": "' + env_id + '"}',
            f"{env_id}:timestamp": timestamp,
        }
        
        # Insert key-value pairs
        for key, value in data_to_insert.items():
            r.set(key, value)
            print(f"  ✓ Set {key} = {value}")
        
        # # Insert list data
        # list_key = f"{env_id}:list:items"
        # r.delete(list_key)  # Clear existing list
        # for i in range(5):
        #     r.lpush(list_key, f"item-{i}")
        # print(f"  ✓ Created list {list_key} with 5 items")
        
        # # Insert hash data
        # hash_key = f"{env_id}:hash:config"
        # r.hset(hash_key, mapping={
        #     "environment": env_id,
        #     "host": REDIS_HOST,
        #     "timestamp": timestamp,
        #     "version": "1.0"
        # })
        # print(f"  ✓ Created hash {hash_key}")
        
        # # Insert set data
        # set_key = f"{env_id}:set:tags"
        # r.sadd(set_key, "production", "redis", "traefik", env_id)
        # print(f"  ✓ Created set {set_key}")
        
        # # Insert sorted set data
        # zset_key = f"{env_id}:zset:scores"
        # r.zadd(zset_key, {"alice": 100, "bob": 85, "charlie": 92})
        # print(f"  ✓ Created sorted set {zset_key}")
        
        # # Set expiring key
        # expire_key = f"{env_id}:temp:session"
        # r.setex(expire_key, 300, f"Temporary data for {env_id}")  # Expires in 5 minutes
        # print(f"  ✓ Set expiring key {expire_key} (TTL: 300s)")
        
        print(f"\n✓ Successfully inserted all test data to {env_id}")
        
        # Show summary
        total_keys = len(r.keys(f"{env_id}:*"))
        print(f"\nSummary: {total_keys} keys in {env_id} namespace")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
