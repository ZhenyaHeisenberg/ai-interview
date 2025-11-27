**bash**
docker build -t ai-interview .

docker run -d --rm -p 5000:5000 --name ai-interview-app ai-interview

start http://localhost:5000