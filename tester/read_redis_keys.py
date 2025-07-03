#!/usr/bin/env python3
import redis
import ssl
import socket
import sys
import json

# CONFIG
REDIS_HOST = "x.x.x.x"  # Your NLB IP
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
    
    print(f"Redis Read Tester - Environment: {env_id}")
    print("="*50)
    
    try:
        # Connect to Redis
        r, sni = connect_to_redis(env_id)
        r.ping()
        print(f"✓ Connected to {sni}")
        
        # Read all keys for this environment
        pattern = f"{env_id}:*"
        keys = r.keys(pattern)
        
        if not keys:
            print(f"\n⚠ No keys found matching pattern '{pattern}'")
            print("  Run the insert tester first to add some data!")
            return
        
        print(f"\n✓ Found {len(keys)} keys in {env_id}:")
        print("-" * 50)
        
        # Read different types of data
        for key in sorted(keys):
            key_str = key.decode()
            key_type = r.type(key).decode()
            
            print(f"\n📍 Key: {key_str}")
            print(f"   Type: {key_type}")
            
            # if key_type == "string":
            #     value = r.get(key)
            #     print(f"   Value: {value.decode()}")
                
            #     # Check TTL
            #     ttl = r.ttl(key)
            #     if ttl > 0:
            #         print(f"   TTL: {ttl} seconds")
                
            # elif key_type == "list":
            #     length = r.llen(key)
            #     values = r.lrange(key, 0, -1)
            #     print(f"   Length: {length}")
            #     print(f"   Values: {[v.decode() for v in values]}")
                
            # elif key_type == "hash":
            #     hash_data = r.hgetall(key)
            #     print("   Fields:")
            #     for field, value in hash_data.items():
            #         print(f"     {field.decode()}: {value.decode()}")
                    
            # elif key_type == "set":
            #     members = r.smembers(key)
            #     print(f"   Members: {[m.decode() for m in members]}")
                
            # elif key_type == "zset":
            #     members = r.zrange(key, 0, -1, withscores=True)
            #     print("   Members (with scores):")
            #     for member, score in members:
            #         print(f"     {member.decode()}: {score}")
        
        # Show Redis info
        print("\n" + "="*50)
        print("Redis Server Info:")
        info = r.info('server')
        print(f"  Version: {info.get('redis_version', 'unknown')}")
        print(f"  Uptime: {info.get('uptime_in_days', 'unknown')} days")
        
        # Show memory usage
        memory_info = r.info('memory')
        used_memory_human = memory_info.get('used_memory_human', 'unknown')
        print(f"  Memory Used: {used_memory_human}")
        
        # Test cross-environment isolation
        print(f"\n🔒 Environment Isolation Test:")
        other_envs = [e for e in ["env1", "env2", "env3"] if e != env_id]
        for other_env in other_envs:
            other_keys = r.keys(f"{other_env}:*")
            if other_keys:
                print(f"  ⚠ WARNING: Found {len(other_keys)} keys from {other_env} in {env_id}!")
            else:
                print(f"  ✓ No keys from {other_env} found (correct isolation)")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
