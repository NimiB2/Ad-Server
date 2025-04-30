# Server Setup

This document provides instructions for setting up and deploying the Flask Ad Server.

## Prerequisites

- Python 3.9 or higher
- MongoDB Atlas account
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Local Development Setup

### 1. Clone or Download the Repository

```bash
git clone https://github.com/yourusername/ad-server.git
cd ad-server
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate the virtual environment:

- On Windows:
  ```bash
  venv\Scripts\activate
  ```

- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

The project dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This will install:
- flask
- flasgger
- pymongo
- python-dotenv
- email-validator

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```
DB_CONNECTION_STRING=cluster0.example.mongodb.net
DB_NAME=adserver
DB_USERNAME=dbuser
DB_PASSWORD=dbpassword
```

Replace the values with your MongoDB Atlas credentials.

### 5. Run the Server Locally

```bash
python app.py
```

By default, the server will run on port 1993. You can access it at http://localhost:1993.

To access the Swagger documentation, go to http://localhost:1993/apidocs/.

## MongoDB Atlas Setup

### 1. Create a MongoDB Atlas Account

If you don't have one already, sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).

### 2. Create a Cluster

- Select your preferred cloud provider and region
- Choose the free tier if you're just getting started
- Assign a cluster name (e.g., "ad-server-cluster")

### 3. Create a Database User

- Go to Security > Database Access
- Add a new database user with read/write permissions
- Generate a secure password

### 4. Set Network Access

- Go to Security > Network Access
- Add your IP address or allow access from anywhere (for development only)

### 5. Get Connection String

- Go to Clusters > Connect
- Select "Connect your application"
- Copy the connection string
- Replace `<password>` with your database user's password
- Use this string in your `.env` file

## Deployment Options

The Flask Ad Server can be deployed to various platforms. Here are instructions for some common options:

### Vercel Deployment

The repository includes a `vercel.json` file for easy deployment to Vercel:

```json
{
    "version": 2,
    "builds": [
        {
            "src": "app.py",
            "use":"@vercel/python"
        }
    ],
    "routes":[
        {
            "src": "/(.*)",
            "dest":"app.py"
        }
    ]
}
```

To deploy to Vercel:

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. Set environment variables in the Vercel dashboard:
   - Go to your project settings
   - Add environment variables for DB_CONNECTION_STRING, DB_NAME, DB_USERNAME, and DB_PASSWORD

### Heroku Deployment

1. Create a `Procfile` in the project root:
   ```
   web: gunicorn app:app
   ```

2. Add gunicorn to requirements.txt:
   ```
   gunicorn
   ```

3. Install the Heroku CLI and deploy:
   ```bash
   heroku login
   heroku create your-ad-server
   git push heroku main
   ```

4. Set environment variables:
   ```bash
   heroku config:set DB_CONNECTION_STRING=your_connection_string
   heroku config:set DB_NAME=your_db_name
   heroku config:set DB_USERNAME=your_username
   heroku config:set DB_PASSWORD=your_password
   ```

## Server Configuration

### Port Configuration

The server listens on port 1993 by default, but you can change this by setting the PORT environment variable:

```python
# In app.py
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 1993))
    app.run(debug=True, port=port)
```

### Debug Mode

In production, you should disable debug mode:

```python
# For production
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 1993))
    app.run(debug=False, host='0.0.0.0', port=port)
```

### MongoDB Connection

The server uses the `MongoConnectionManager` class to handle database connections:

```python
class MongoConnectionManager:
    __db = None

    @staticmethod
    def init_db():
        """
        Initialize the database connection
        """
        if MongoConnectionManager.__db is None:
            # Create a new client and connect to the server
            client = MongoClient(Mongo_URI, server_api=ServerApi('1'))
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
                MongoConnectionManager.__db = client[DB_NAME]
            except Exception as e:
                print(e)
        return MongoConnectionManager.__db    

    @staticmethod
    def get_db():
        """
        Get the database connection
        """       
        if MongoConnectionManager.__db is None:
            MongoConnectionManager.init_db()
        return MongoConnectionManager.__db
```

## Health Monitoring

To add a health check endpoint:

```python
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check database connection
        db = MongoConnectionManager.get_db()
        db.command('ping')
        return jsonify({'status': 'healthy', 'db_connection': 'ok'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
```

## Scaling Considerations

When scaling the Flask Ad Server for production:

1. **Database Indexes**: Ensure all collections have proper indexes for query patterns
2. **Connection Pooling**: Use MongoDB's connection pooling for efficient resource utilization
3. **Load Balancing**: Deploy multiple instances behind a load balancer
4. **Caching**: Implement caching for frequently accessed data
5. **Monitoring**: Set up monitoring for performance and errors
6. **Logging**: Implement comprehensive logging for debugging and audit trails

## Next Steps

After setting up the server, proceed to:

1. [Database Schema](database-schema.md) - Understand the data structure
2. [API Reference](api-reference.md) - Learn about the available endpoints
3. [SDK Support](sdk-support.md) - See how the server integrates with the Android SDK
