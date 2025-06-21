### Running the Server with Docker Compose

This project includes a production-ready `docker-compose.yml` file to run the `fabric-mcp` server and its required `fabric` dependency. This method encapsulates both services in isolated, managed containers.

#### Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

#### First-Time Setup

You only need to perform these steps once.

1.  **Create the Fabric API Key Secret**

    The `docker-compose.yml` setup uses Docker Secrets to securely manage the Fabric API key. Create a file named `fabric_api_key.txt` in the root of this project:

    ```bash
    echo "your-secret-fabric-api-key" > fabric_api_key.txt
    ```
    Replace `your-secret-fabric-api-key` with the actual key used by your Fabric instance.

2.  **Populate the Fabric Configuration Volume**

    The setup uses a named Docker volume (`fabric_config`) to store your Fabric patterns and configuration. This ensures your data persists even if the container is removed.

    If your Fabric configuration is in the default location (`~/.config/fabric`), run the following command to copy it into the Docker volume. If your configuration is elsewhere, replace the path accordingly.

    ```bash
    docker run --rm -v ~/.config/fabric:/source -v fabric_config:/dest alpine sh -c "cp -r /source/. /dest/"
    ```
    *Note: The `docker-compose.yml` file ensures the volume is always named `fabric_config`, so this command will work regardless of your project's directory name.*

#### Starting and Stopping the Services

1.  **Build and Start the Services**

    With the secret and volume prepared, you can now build and start the containers in detached mode:

    ```bash
    docker-compose up --build -d
    ```

    The `fabric-mcp` service will now be running and available on `http://localhost:8000`.

2.  **Accessing the Server**

    You can now send MCP requests to `http://localhost:8000/message`.

3.  **Viewing Logs**

    To follow the logs for all running services:
    ```bash
    docker-compose logs -f
    ```
    To view logs for a specific service (e.g., `fabric-mcp`):
    ```bash
    docker-compose logs -f fabric-mcp
    ```

4.  **Stopping the Services**

    To stop and remove the containers and network:
    ```bash
    docker-compose down
    ```
    Your `fabric_config` volume will not be deleted, so your patterns are safe.
