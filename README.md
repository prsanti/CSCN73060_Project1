# Create environment (Python 3.14.2)
```
python -m venv venv
```

# Activate
## Windows
```
venv\Scripts\activate
```

## Mac
```
source venv/bin/activate
```

# Install Requirements
```
pip install -r requirements.txt
```

# Build Docker Image in root directory
```
docker build -t helpdesk .
```

# Run Docker Container in root directory
```
docker run -p 7500:7500 helpdesk
```