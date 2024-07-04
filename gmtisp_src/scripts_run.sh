# 2. create Variables
# DATABASE="testdb"
# USERNAME="radius"
# PASSWORD="aaaAAA123"


# # 3. Create database if it doesn't exist, and grant privileges
# psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname = '$DATABASE';" | grep -q 1 || psql -U postgres -c "CREATE DATABASE $DATABASE;"

# # Create user and grant privileges
# psql -U postgres <<EOF
# DO \$\$
# BEGIN
#     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$USERNAME') THEN
#         CREATE USER $USERNAME WITH PASSWORD '$PASSWORD';
#     END IF;
# END
# \$\$;
# GRANT ALL PRIVILEGES ON DATABASE $DATABASE TO $USERNAME;
# ALTER USER $USERNAME CREATEDB;
# EOF

# echo "User $USERNAME created and granted privileges on $DATABASE."

# DATABASES=("db_gies" "db_gigmeg" "db_gmtisp")

# # Create user and grant privileges
# psql -U postgres <<EOF
# $(for db in "${DATABASES[@]}"; do echo "GRANT ALL PRIVILEGES ON DATABASE $db TO $USERNAME;"; done)
# EOF

# echo "User $USERNAME created and granted privileges on ${DATABASES[*]}."