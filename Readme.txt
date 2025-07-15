docker build -t lead-management-app .

docker run -d -p 5000:5000 --name lead-app -v ./data:/app/data lead-management-app