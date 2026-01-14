DOCKER run cmd

```
docker build -t my-livekit-agent .

docker run -it --rm  -v $(pwd)/src:/app/src  my-livekit-agent bash
```