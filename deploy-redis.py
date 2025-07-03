import subprocess
from string import Template

# List of ENV_IDs to deploy
env_ids = ["env1", "env2", "env3"]

# YAML template for Deployment, Service, and IngressRouteTCP
yaml_template = Template("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-${ENV_ID}
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
      env: "${ENV_ID}"
  template:
    metadata:
      labels:
        app: redis
        env: "${ENV_ID}"
    spec:
      containers:
        - name: redis
          image: redis:7
          ports:
            - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis-${ENV_ID}
  namespace: default
spec:
  selector:
    app: redis
    env: "${ENV_ID}"
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
---
apiVersion: traefik.io/v1alpha1
kind: IngressRouteTCP
metadata:
  name: redis-${ENV_ID}-route
  namespace: default
spec:
  entryPoints:
    - redis
  routes:
    - match: HostSNI(`redis-${ENV_ID}.redis.local`)
      services:
        - name: redis-${ENV_ID}
          port: 6379
  tls:
    secretName: redis-default-cert
""")

# Apply each ENV_ID's configuration
for env_id in env_ids:
    yaml_content = yaml_template.substitute(ENV_ID=env_id)
    print(f"Deploying Redis for ENV_ID: {env_id}")
    
    try:
        proc = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=yaml_content.encode("utf-8"),
            check=True,
            capture_output=True
        )
        print(proc.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error deploying {env_id}:\n{e.stderr.decode()}")
