import docker

client = docker.from_env()

try:
    container = client.containers.run(
        'nginx:alpine',
        name='test_port_7000',
        detach=True,
        ports={'80/tcp': 7000}
    )
    print(f'✅ Success! Container ID: {container.id}')
    print(f'Puerto 7000 está DISPONIBLE')
    
    # Limpiar
    container.stop()
    container.remove()
    print('🧹 Container cleaned up')
    
except Exception as e:
    print(f'❌ Error: {type(e).__name__}')
    print(f'Message: {str(e)}')
