# Create or Update Your Deployment Script:

#!/bin/bash

# Ensure the script stops if any command fails
set -e

# Activate the virtual environment
# source v0/bin/activate

# Run migrations
echo "Making migrations..."
python manage.py makemigrations

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Run the custom management command to set up databases
echo "Setting up organization databases..."
python manage.py setup_org_databases

# # Run tests
# echo "Running tests..."
# python manage.py test

echo "Deployment script completed successfully."

# echo "Create superuser."
# python manage.py createsuperuser

# echo "Show migrations."
# python manage.py showmigrations


# Steps to Run the Deployment Script
# 1. Make sure your deployment script (deploy.sh) is executable using below command in terminal.
# chmod +x deploy.sh
# 2. Run the Script: Execute the script from your terminal.
# ./deploy.sh
# This will:
# Activate your virtual environment.
# Run Django migrations to apply any changes to your database schema.
# Run your custom management command setup_org_databases to configure organization-specific databases.
# This command will continuously output the last lines of the deployment.log file, 
# updating in real-time as new log entries are added. 
# tail -f deployment.log
