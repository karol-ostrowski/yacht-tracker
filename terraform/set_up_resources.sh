terraform apply -auto-approve
echo "AZURE_CONNECTION_STRING=$(terraform output -raw connection_string)" > .env
echo "AZURE_CONTAINER_NAME=$(terraform output -raw container_name)" >> .env