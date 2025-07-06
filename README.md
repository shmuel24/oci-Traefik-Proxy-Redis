# Traefik TCP Proxy for Redis with SNI-based Isolation on OKE

This project demonstrates how to deploy multiple Redis instances on an Oracle Kubernetes Engine (OKE) cluster and expose them via Traefik TCP routing with TLS and SNI-based routing. It enables isolating environments (like `env1`, `env2`, etc.) using a single external Network Load Balancer.

---

## Project Structure

```
Traefik_proxy_for_redis/
├── deploy_redis.py                # Deploys multiple Redis + IngressRouteTCP
├── traefik-values.yaml            # Helm values for Traefik TCP proxy setup
├── Traefik_CRDS_and_commands.txt  # Manual commands for CRDs and certs
└── testers/
    ├── insert_redis_keys.py       # Inserts test data using SNI TLS connection
    └── read_redis_keys.py         # Reads and validates test data
```

---

## Prerequisites

Before you begin, ensure you have the following:

- A running [OKE cluster](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- `kubectl` configured for the OKE cluster
- Helm installed
- Python 3.8+ with `redis` library installed:
  ```bash
  pip install redis
  ```
- OpenSSL installed
- Traefik v3.x installed via Helm (used as a TCP proxy, not just ingress)

---

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/shmuel24/oci-Traefik-Proxy-Redis.git
cd Traefik_proxy_for_redis
```

### 2. Create a TLS Certificate for `*.redis.local`

```bash
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -days 365 \
  -subj "/CN=*.redis.local"
```

### 3. Create a Kubernetes Secret for the TLS Certificate

```bash
kubectl create secret generic redis-default-cert \
  --from-file=tls.crt=tls.crt \
  --from-file=tls.key=tls.key \
  -n traefik
```

### 4. Deploy Traefik as TCP Proxy

Use the provided `traefik-values.yaml` file:

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update

helm install traefik traefik/traefik \
  --namespace traefik --create-namespace \
  -f traefik-values.yaml
```

This sets up a TCP entrypoint on port 6379 with SNI-based TLS routing, exposed via an OCI NLB.

### 5. Install Traefik CRDs and RBAC

```bash
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.4/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.4/docs/content/reference/dynamic-configuration/kubernetes-crd-rbac.yml
```

### 6. Deploy Redis Pods per Environment

Run the following script to deploy Redis for multiple environments (e.g., `env1`, `env2`, ...):

```bash
python3 deploy_redis.py
```

This creates:

- One Redis Deployment per environment
- A matching Service
- A Traefik `IngressRouteTCP` for each environment based on HostSNI(`redis-<env>.redis.local`)

---

## Testing

### Insert Test Data

```bash
python3 testers/insert_redis_keys.py env1
```

This connects using SNI `redis-env1.redis.local` and inserts multiple keys for the namespace `env1`.

### Read and Verify Data

```bash
python3 testers/read_redis_keys.py env1
```

This prints all keys, their types, and checks for cross-environment isolation.

---

## Access Pattern

All Redis pods are exposed through a single NLB IP using TLS + SNI.

- Redis client must support SNI and TLS
- Example hostnames:
  - `redis-env1.redis.local`
  - `redis-env2.redis.local`

---

## Notes

- Redis image used: `redis:7`
- Traefik terminates TLS and matches based on SNI
- Each environment is fully isolated via key namespace prefix (`env1:*`)
- You can add more environments by editing the `env_ids` list in `deploy_redis.py`

---

## Disclaimer

Use of the code in this repository is at your own responsibility only.
