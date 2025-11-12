"""
Funciones para gestionar el repositorio Git
"""
import os
from git import Repo


def inicializar_repo(repo_dir, repo_url, token):
    """
    Clona el repositorio si no existe o lo actualiza si ya existe.
    
    Args:
        repo_dir: Directorio local del repositorio
        repo_url: URL del repositorio
        token: Token de acceso a GitHub
        
    Returns:
        Repo: Objeto del repositorio Git
    """
    if not os.path.exists(repo_dir):
        auth_url = f"https://{token}@{repo_url.replace('https://', '')}"
        Repo.clone_from(auth_url, repo_dir)
    
    repo = Repo(repo_dir)
    repo.remote(name="origin").pull()
    
    return repo


def commit_y_push(repo, mensaje_commit):
    """
    Realiza commit y push de los cambios al repositorio.
    
    Args:
        repo: Objeto del repositorio Git
        mensaje_commit: Mensaje del commit
    """
    repo.git.add(".")
    repo.index.commit(mensaje_commit)
    origin = repo.remote(name="origin")
    origin.push()
