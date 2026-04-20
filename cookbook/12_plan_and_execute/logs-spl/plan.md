Here is a numbered list of concrete steps to build a REST API for a todo app:

1. **Set up project structure and dependencies**: 
   - Create a new project folder with a standard directory structure (e.g., `src`, `tests`, `config`).
   - Install required dependencies using npm or yarn (e.g., Express.js, Mongoose).

2. **Design and implement API endpoints**:
   - Define a set of RESTful API endpoints for CRUD operations (create, read, update, delete) on todo items.
   - Create API routes using Express.js and implement endpoint handlers.

3. **Implement data storage and retrieval**:
   - Choose a database to store todo data (e.g., MongoDB).
   - Set up Mongoose to interact with the chosen database and define schema for todo items.
   - Implement data retrieval and manipulation logic using Mongoose.

4. **Add authentication and authorization**:
   - Integrate a library like Passport.js to handle authentication.
   - Implement authentication middleware to protect API endpoints.
   - Define authentication routes and handle user registration, login, and logout.

5. **Test API endpoints and functionality**:
   - Write unit tests using Jest or Mocha for individual endpoint handlers.
   - Use Postman or a similar tool to test the entire API, ensuring proper routing and response formatting.

6. **Deploy and serve the API**:
   - Choose a deployment strategy (e.g., Docker, AWS Elastic Beanstalk).
   - Set up environment variables for production (e.g., database connection strings, authentication tokens).
   - Serve the API using Express.js, optionally behind a reverse proxy or load balancer.