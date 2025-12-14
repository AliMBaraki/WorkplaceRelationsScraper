The NoSQL DB of my choice was AWS DynamoDB, local blob storage was used with docker containers (had it not been explicitly stated I would have used AWS S3 buckets), and AWS Lambda was used to host and orchestrate the application. AWS CloudWatch was used for logging & monitoring as well as AWS event bridge for scheduling.

To use this project locally, you must install and sign in to docker desktop and enter the following commands in your terminal:
Step 0: 
  -docker login
  -aws configure
step 1: 
  docker-compose up --build
